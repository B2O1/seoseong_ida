# cafes/views.py (public_store_name → crawled_store_name 전면 교체)
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import F, Q, Window
from django.db.models import (
    BooleanField, IntegerField, SmallIntegerField, PositiveIntegerField, FloatField,
    CharField, TextField
)
from .models import DfCafeFull
import hashlib, re
from django.core.paginator import Paginator
from django.db.models.functions import RowNumber

class FindByMapView(TemplateView):
    template_name = "cafes/findbymap.html"

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


def _field_in(model, candidates):
    """모델에 존재하는 첫 번째 후보 필드명을 반환"""
    field_names = {f.name for f in model._meta.get_fields() if hasattr(f, "attname")}
    for c in candidates:
        if c in field_names:
            return c
    return None

class CategoryView(TemplateView):
    template_name = "cafes/category.html"
    PAGE_SIZE_DEFAULT = 12
    PAGE_SIZE_MAX = 60

    # 버튼 라벨 → 실제 컬럼
    KOR2COL = {
        "쾌좋카": "comfy_cafe",
        "혼좋카": "solo_cafe",
        "책좋카": "book_cafe",
        "이걸안카": "unique_cafe",
        "단좋카": "group_cafe",
        "커맛카": "coffee_taste_cafe",
        "카공카": "study_cafe",
        "화청카": "bright_cafe",
        "분좋카": "mood_cafe",
        "디맛카": "desset_taste_cafe",  # DB 컬럼명 주의
        "가좋카": "cheap_cafe",
        "반동카": "animal_cafe",
        "밤샘카페": "night_cafe",
        "한옥": "hanok_cafe",
    }

    NAME_CANDS = ["crawled_store_name"]
    TIME_CANDS = ["visit_time"]   # visit_time → time 별칭
    ADDR_CANDS = ["address"]
    RATE_CANDS = ["rating"]

    # ---------- 내부 유틸 ----------
    def _field_in(self, model, candidates):
        fields = {f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)}
        for c in candidates:
            if c in fields:
                return c
        return None

    def _clean_rating(self, v):
        if v is None:
            return None
        m = _num_re.search(str(v))
        try:
            return float(m.group(1)) if m else None
        except Exception:
            return None

    def _truthy_q(self, field_name: str) -> Q:
        """필드 타입에 맞는 '참 값' 조건 생성"""
        try:
            f = DfCafeFull._meta.get_field(field_name)
        except Exception:
            return Q()

        if isinstance(f, BooleanField):
            return Q(**{field_name: True})
        if isinstance(f, (IntegerField, SmallIntegerField, PositiveIntegerField, FloatField)):
            return Q(**{f"{field_name}__gt": 0})
        if isinstance(f, (CharField, TextField)):
            return Q(**{f"{field_name}__regex": r"^(?:1|y|Y|t|T|true|TRUE)$"})
        return ~Q(**{f"{field_name}__isnull": True})

    # ---------- 쿼리셋 구성 ----------
    def _build_queryset(self):
        name_f = self._field_in(DfCafeFull, self.NAME_CANDS)
        time_f = self._field_in(DfCafeFull, self.TIME_CANDS)
        addr_f = self._field_in(DfCafeFull, self.ADDR_CANDS)
        rate_f = self._field_in(DfCafeFull, self.RATE_CANDS)

        if not name_f:
            return DfCafeFull.objects.none(), None, None, None, None, {}

        qs = DfCafeFull.objects.all()

        # ✅ 주소 없는(빈 문자열/NULL) 카페 제외
        if addr_f:
            qs = qs.exclude(**{f"{addr_f}__isnull": True}).exclude(**{f"{addr_f}__exact": ""})

        # 실제 존재하는 카테고리 컬럼만 사용
        model_fields = {f.name for f in DfCafeFull._meta.get_fields() if getattr(f, "concrete", False)}
        cat_cols = {kor: col for kor, col in self.KOR2COL.items() if col in model_fields}

        # 검색어(q): 이름 + 영업시간
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qf = Q(**{f"{name_f}__icontains": q})
            if time_f:
                qf |= Q(**{f"{time_f}__icontains": q})
            qs = qs.filter(qf)

        # 카테고리 필터
        cats = self.request.GET.getlist("cat")
        if cats:
            or_q = Q()
            for kor in cats:
                col = self.KOR2COL.get(kor)
                if col and col in model_fields:
                    or_q |= self._truthy_q(col)
            if or_q:
                qs = qs.filter(or_q)
        else:
            # cat 파라미터 없어도 '어느 카테고리든 하나 이상 참'만 노출
            any_q = Q()
            for _, col in cat_cols.items():
                any_q |= self._truthy_q(col)
            if any_q:
                qs = qs.filter(any_q)

        # ---- 대표 1행만 남기기 (윈도우) ----
        win_order = []
        if self._field_in(DfCafeFull, ["total_review_count"]):
            win_order.append(F("total_review_count").desc(nulls_last=True))
        if self._field_in(DfCafeFull, ["final_crawl_count"]):
            win_order.append(F("final_crawl_count").desc(nulls_last=True))
        win_order.append(F(name_f).asc())

        partition_by = [F(name_f)]
        if addr_f:
            partition_by.append(F(addr_f))

        qs = qs.annotate(
            _rn=Window(
                expression=RowNumber(),
                partition_by=partition_by,
                order_by=win_order,
            )
        ).filter(_rn=1)

        # 화면용 별칭
        if name_f != "name":
            qs = qs.annotate(name=F(name_f))
        if time_f:
            qs = qs.annotate(time=F(time_f))
        if addr_f and addr_f != "address":
            qs = qs.annotate(address=F(addr_f))
        if rate_f and rate_f != "rating":
            qs = qs.annotate(rating=F(rate_f))

        # 최종 정렬
        qs = qs.order_by("name" if name_f != "name" else name_f)

        return qs, name_f, time_f, addr_f, rate_f, cat_cols

    # ---------- 컨텍스트 ----------
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # 페이지 크기/번호
        try:
            page_size = int(self.request.GET.get("page_size", self.PAGE_SIZE_DEFAULT))
        except Exception:
            page_size = self.PAGE_SIZE_DEFAULT
        page_size = max(10, min(page_size, self.PAGE_SIZE_MAX))

        try:
            page_number = int(self.request.GET.get("page", 1))
        except Exception:
            page_number = 1
        page_number = max(1, page_number)

        qs, name_f, time_f, addr_f, rate_f, cat_cols = self._build_queryset()

        if qs is None or name_f is None:
            paginator = Paginator([], page_size)
            page_obj = paginator.get_page(page_number)
            ctx["page_obj"] = page_obj
            ctx["cafes"] = page_obj.object_list
            # 필터 유지용 쿼리스트링
            keep = self.request.GET.copy()
            keep.pop('page', None)
            qs_keep = keep.urlencode()
            ctx["qs_keep"] = f"&{qs_keep}" if qs_keep else ""
            return ctx

        # values 선택
        select_fields = ["name" if name_f != "name" else name_f]
        if time_f:
            select_fields.append("time")
        if addr_f:
            select_fields.append("address" if addr_f != "address" else "address")
        if rate_f:
            select_fields.append("rating" if rate_f != "rating" else "rating")
        # 카테고리 컬럼 추가
        model_fields = {f.name for f in DfCafeFull._meta.get_fields() if getattr(f, "concrete", False)}
        cat_cols = {kor: col for kor, col in self.KOR2COL.items() if col in model_fields}
        if cat_cols:
            select_fields += list(cat_cols.values())

        raw = list(qs.values(*select_fields))

        # 선택된 cat만 표시하고 싶다면 교집합 적용
        cats_filter = set(self.request.GET.getlist("cat"))

        # 안전망: (name,address) 중복 제거
        seen = set()
        rows = []
        for r in raw:
            name_key = "name" if "name" in r else name_f
            name = (r.get(name_key) or "").strip()
            addr = (r.get("address") or "").strip() if "address" in r else ""

            key = (name, addr)
            if key in seen:
                continue
            seen.add(key)

            cats_for_row = []
            for kor, col in cat_cols.items():
                val = r.get(col)
                if val in (1, True, "1", "Y", "y", "T", "t", "true", "TRUE"):
                    cats_for_row.append(kor)

            if cats_filter:
                cats_for_row = [k for k in cats_for_row if k in cats_filter]

            rows.append({
                "name": name,
                "time": (r.get("time") or "영업시간 정보가 없습니다."),
                "address": addr,
                "rating": self._clean_rating(r.get("rating")) if "rating" in r else None,
                "cats": cats_for_row,
                "cats_display": " · ".join(cats_for_row),
            })

        paginator = Paginator(rows, page_size)
        page_obj = paginator.get_page(page_number)
        ctx["page_obj"] = page_obj
        ctx["cafes"] = page_obj.object_list

        # 필터 유지용 쿼리스트링 (page만 제외)
        keep = self.request.GET.copy()
        keep.pop('page', None)
        qs_keep = keep.urlencode()
        ctx["qs_keep"] = f"&{qs_keep}" if qs_keep else ""

        return ctx