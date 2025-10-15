from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import F, Q
from .models import DfCafeFull
import requests
import hashlib, re
from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.conf import settings
import requests
from django.db import connection
from django.db.models import Q, F, Window
from django.db.models.functions import RowNumber, Coalesce


def place_photo_redirect(request, place_id: str, photo_id: str):
    name = f"places/{place_id}/photos/{photo_id}"
    url = f"https://places.googleapis.com/v1/{name}/media"
    params = {"maxWidthPx": request.GET.get("w", 640)}
    headers = {"X-Goog-Api-Key": settings.GOOGLE_API_KEY}
    r = requests.get(url, headers=headers, params=params, timeout=8)
    if r.ok and r.headers.get("Content-Type","").startswith("application/json"):
        data = r.json()
        if "photoUri" in data:
            return HttpResponseRedirect(data["photoUri"])
    elif r.is_redirect:
        return HttpResponseRedirect(r.headers["Location"])
    raise Http404("Photo not available")

class FindByMapView(TemplateView):
    template_name = "cafes/findbymap.html"

class CategoryView(TemplateView):
    template_name = "cafes/category.html"

_num_re = re.compile(r"(\d+(?:\.\d+)?)")

def _clean_rating(val):
    if val is None:
        return None
    m = _num_re.search(str(val))
    try:
        return float(m.group(1)) if m else None
    except Exception:
        return None

def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None
# ===============================
# 헬퍼: 정렬키(별점 desc, 리뷰수 desc, 이름 asc-ish)
# ===============================
def _rank_key(item):
    rating = item.get("rating")
    has_rating = rating is not None
    name = (item.get("crawled_store_name") or "").lower()
    # reverse=True로 정렬할 거라 rating/리뷰수는 큰 값이 위로 감
    # name은 reverse=True 때문에 Z→A가 되지만 영향은 미미 (동점자 tie-breaker 용)
    return (has_rating, rating if rating is not None else -1.0, name)

# ===============================
# 헬퍼: 카테고리 균등 분포(라운드로빈)
# ===============================
def _balance_by_categories(items, cat_keys, page_size):
    """
    items: [{..., 'cats': {'book_cafe':1, ...}}]  # 내부 cats 딕셔너리 포함
    cat_keys: 균등 분포를 원하는 카테고리 키 리스트
    """
    # 카테고리별 버킷 구성(각 버킷 내부는 기본 랭킹으로 정렬)
    buckets = []
    for k in cat_keys:
        lst = [it for it in items if it.get("cats", {}).get(k) == 1]
        lst.sort(key=_rank_key, reverse=True)
        if lst:
            buckets.append([k, lst])

    used = set()
    out = []

    i = 0
    guard = 0
    while len(out) < page_size and buckets and guard < page_size * 50:
        k, lst = buckets[i % len(buckets)]
        # 이미 사용된 항목 제거
        while lst and lst[0]["id"] in used:
            lst.pop(0)
        if lst:
            it = lst.pop(0)
            out.append(it)
            used.add(it["id"])
        else:
            # 버킷이 비었으면 제거
            buckets.pop(i % len(buckets))
            i -= 1
        i += 1
        guard += 1

    # 모자라면 남은 것 중 랭킹 높은 순으로 채우기
    if len(out) < page_size:
        remain = [it for it in items if it["id"] not in used]
        remain.sort(key=_rank_key, reverse=True)
        for it in remain:
            if len(out) >= page_size:
                break
            out.append(it)
            used.add(it["id"])

    return out

# ===============================
# 메인: cafes_api (별점 높은 순 + 카테고리 균등 분포)
# ===============================
def cafes_api(request):
    """
    GET:
      - bbox=minLng,minLat,maxLng,maxLat (좌표 컬럼 있을 때만 사용)
      - zoom=int
      - cats=CSV  (예: cats=book_cafe,study_cafe)
      - page_size=int (기본 500, 최대 1000)
      - page_token=offset (기본 0)
    """
    bbox = request.GET.get("bbox")
    zoom = int(request.GET.get("zoom", 12))
    page_size = max(50, min(int(request.GET.get("page_size", 2000)), 2000))
    try:
        offset = int(request.GET.get("page_token", "0"))
        if offset < 0:
            offset = 0
    except Exception:
        offset = 0

    cats_raw = (request.GET.get("cats") or "").strip()
    cat_keys = [c for c in cats_raw.split(",") if c]

    CATEGORY_KEYS = [
        "comfy_cafe","solo_cafe","book_cafe","unique_cafe","group_cafe",
        "coffee_taste_cafe","study_cafe","bright_cafe","mood_cafe",
        "dessert_taste_cafe","cheap_cafe","animal_cafe","night_cafe","hanok_cafe",
    ]

    model_fields = {f.name for f in DfCafeFull._meta.get_fields() if getattr(f, "concrete", False)}

    # 좌표 컬럼 확인
    has_latlng   = ("lat" in model_fields and "lng" in model_fields)
    has_latlongw = ("lat_n" in model_fields and "long_w" in model_fields)

    base_fields = [
        "crawled_store_name",  # 이름
        "address","rating",
    ]
    if has_latlng:
        base_fields += ["lat","lng"]
    if has_latlongw:
        base_fields += ["lat_n","long_w"]

    if "total_review_count" in model_fields:
        base_fields.append("total_review_count")
    if "final_crawl_count" in model_fields:
        base_fields.append("final_crawl_count")

    wanted = base_fields + [k for k in CATEGORY_KEYS if k in model_fields]
    use_fields = [f for f in wanted if f in model_fields]

    qs = DfCafeFull.objects.all()

    # bbox 필터 (좌표 있을 때만)
    if bbox and (has_latlng or has_latlongw):
        try:
            min_lng, min_lat, max_lng, max_lat = map(float, bbox.split(","))
        except Exception:
            return HttpResponseBadRequest("invalid bbox")
        if has_latlng:
            qs = qs.filter(lat__gte=min_lat, lat__lte=max_lat,
                           lng__gte=min_lng, lng__lte=max_lng)
        else:
            qs = qs.filter(lat_n__gte=min_lat, lat_n__lte=max_lat,
                           long_w__gte=min_lng, long_w__lte=max_lng)

    # 카테고리 OR 필터
    if cat_keys:
        q = Q()
        for k in cat_keys:
            if k in model_fields:
                q |= Q(**{k: 1})
        if q:
            qs = qs.filter(q)

    order_for_rep = [
        F("rating").desc(nulls_last=True),
        F("total_review_count").desc(nulls_last=True),
        F("id").desc(),
    ]
    order_final = ["-rating", "-total_review_count", "-id"]

    try:
        if connection.vendor == "postgresql":
            # (Postgres 전용) DISTINCT ON
            qs = qs.order_by("crawled_store_name", "address", *order_for_rep).distinct(
                "crawled_store_name", "address"
            )
        else:
            # (범용) 윈도우 함수 ROW_NUMBER 파티션으로 대표 1행만
            qs = (
                qs.annotate(
                    rn=Window(
                        expression=RowNumber(),
                        partition_by=[F("crawled_store_name"), F("address")],
                        order_by=order_for_rep,
                    )
                )
                .filter(rn=1)
                .order_by(*order_final)
            )
    except Exception:
        # (폴백) DB가 윈도우 함수도 안 될 때는 기존 파이썬 중복제거 경로 사용
        pass

    # 이후 그대로
    raw = list(qs.values(*use_fields)[offset : offset + page_size * 10])
    print(f"[cafes_api] step1: DB에서 {len(raw)}개 불러옴 (offset={offset})")

    # values 추출(여유분 크게: page_size * 10) → (이름,주소) dedupe
    # raw = list(qs.values(*use_fields)[offset : offset + page_size * 10])

    seen = set()
    pool = []
    for r in raw:
        name = (r.get("crawled_store_name") or "").strip()
        addr = (r.get("address") or "").strip()
        key = (name, addr)
        if key in seen:
            continue
        seen.add(key)

        lat = _to_float(r.get("lat")) or _to_float(r.get("lat_n"))
        lng = _to_float(r.get("lng")) or _to_float(r.get("long_w"))
        rating = _clean_rating(r.get("rating"))

        rid = hashlib.md5(f"{name}|{addr}".encode("utf-8")).hexdigest()[:12]

        cats = {}
        for k in CATEGORY_KEYS:
            if k in r:
                cats[k] = 1 if r.get(k) in (1, "1", True, "true", "True") else 0

        item = {
            "id": rid,
            "crawled_store_name": name,
            "address": addr,
            "rating": rating,
            "lat": lat,
            "lng": lng,
            "cats": cats,  # 균등 분포용으로 묶어서 보관
        }
        if "total_review_count" in r:
            item["total_review_count"] = r.get("total_review_count") or 0
        if "final_crawl_count" in r:
            item["final_crawl_count"] = r.get("final_crawl_count") or 0

        pool.append(item)
    print(f"[cafes_api] step2: (이름,주소) 기준 중복제거 후 {len(pool)}개 남음")
    # 기본 스코어링으로 먼저 정렬
    pool.sort(key=_rank_key, reverse=True)

    # 균등 분포 대상 카테고리 결정
    if cat_keys:
        balance_keys = [k for k in cat_keys if any(it["cats"].get(k) == 1 for it in pool)]
    else:
        balance_keys = [k for k in CATEGORY_KEYS if any(it["cats"].get(k) == 1 for it in pool)]

    # 카테고리 균등 분포(라운드로빈)
    balanced = _balance_by_categories(pool, balance_keys, page_size)

    # 응답 형태(flat)로 변환
    final_results = []
    for it in balanced:
        row = {
            "id": it["id"],
            "crawled_store_name": it["crawled_store_name"],
            "address": it["address"],
            "rating": it["rating"],
            "lat": it["lat"],
            "lng": it["lng"],
        }
        row.update(it["cats"])
        if "total_review_count" in it:
            row["total_review_count"] = it["total_review_count"]
        if "final_crawl_count" in it:
            row["final_crawl_count"] = it["final_crawl_count"]
        final_results.append(row)

    # offset 기반 토큰 (균등 분포로 실제 페이지 구성은 서버에서 함)
    # 추천
    next_token = str(offset + page_size) if len(raw) == page_size * 10 else None

    return JsonResponse({"results": final_results, "next_page_token": next_token})