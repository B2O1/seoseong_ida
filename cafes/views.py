# cafes/views.py (public_store_name → crawled_store_name 전면 교체)
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import F, Q
from .models import DfCafeFull
import hashlib, re

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

def cafes_api(request):
    """
    GET:
      - bbox=minLng,minLat,maxLng,maxLat (좌표 컬럼 있을 때만 사용)
      - zoom=int
      - cats=CSV
      - page_size=int (기본 500, 최대 1000)
      - page_token=offset (기본 0)
    """
    bbox = request.GET.get("bbox")
    zoom = int(request.GET.get("zoom", 12))
    page_size = max(50, min(int(request.GET.get("page_size", 500)), 1000))
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
        "crawled_store_name",  # ✅ 이름은 오직 이 필드만 사용
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

    # 정렬: 리뷰수 → 크롤수 → 이름(✅ crawled_store_name)
    order_fields = []
    if "total_review_count" in model_fields:
        order_fields.append(F("total_review_count").desc(nulls_last=True))
    if "final_crawl_count" in model_fields:
        order_fields.append(F("final_crawl_count").desc(nulls_last=True))
    order_fields.append("crawled_store_name")
    qs = qs.order_by(*order_fields)

    # values 추출(여유분 ×5 → (이름,주소) dedupe → page_size 맞춤)
    raw = list(qs.values(*use_fields)[offset : offset + page_size * 5])

    seen = set()
    results = []
    for r in raw:
        name = (r.get("crawled_store_name") or "").strip()  # ✅ 여기서도 교체
        addr = (r.get("address") or "").strip()
        key = (name, addr)
        if key in seen:
            continue
        seen.add(key)

        lat = _to_float(r.get("lat")) or _to_float(r.get("lat_n"))
        lng = _to_float(r.get("lng")) or _to_float(r.get("long_w"))
        rating = _clean_rating(r.get("rating"))

        # ✅ 안정적 가짜 ID도 crawled_store_name 기준
        rid = hashlib.md5(f"{name}|{addr}".encode("utf-8")).hexdigest()[:12]

        cats = {}
        for k in CATEGORY_KEYS:
            if k in r:
                cats[k] = 1 if r.get(k) in (1, "1", True, "true", "True") else 0

        results.append({
            "id": rid,
            "crawled_store_name": name,  # ✅ 응답 키도 교체
            "address": addr,
            "rating": rating,
            "lat": lat,
            "lng": lng,
            **cats,
        })
        if len(results) >= page_size:
            break

    # next_page_token: offset 기반
    next_token = str(offset + page_size) if len(raw) >= page_size else None

    return JsonResponse({"results": results, "next_page_token": next_token})