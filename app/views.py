from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
# from cafes.models import Cafe
from django.conf import settings
import requests
from cafes.models import DfCafeFull

from django.db.models import (
    Exists, OuterRef, FloatField, Q,
    F, Window, CharField, IntegerField
)
from django.db.models.functions import Cast, RowNumber
from django.db.models.expressions import Func, Value

import json
import random
from collections import defaultdict

def home(request):
    flag_fields = [
        'comfy_cafe',
        'solo_cafe',
        'book_cafe',
        'unique_cafe',
        'group_cafe',
        'coffee_taste_cafe',
        'study_cafe',
        'bright_cafe',
        'mood_cafe',
        'dessert_taste_cafe',
        'cheap_cafe',
        'animal_cafe',
        'night_cafe',
        'hanok_cafe',
    ]

    all_recommended = []

    for field in flag_fields:
        # 해당 속성이 1인 카페 중 무작위 2개
        cafes = (
            DfCafeFull.objects
            .filter(**{field: 1})
            .order_by('?')[:2]
        )
        all_recommended.extend(cafes)

    # 전체 결과를 섞어줄 수도 있음
    random.shuffle(all_recommended)

    return render(request, "home.html", {"recommend_cafes": all_recommended})


def search(request):
    return render(request, 'search.html')

def posts_json(request):
    data = list(Post.objects.values('id', 'title', 'content', 'created_at').order_by('-id'))
    return JsonResponse(
        data,
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 2, 'default': str},
        content_type='application/json; charset=utf-8'
    )

User = get_user_model()
# 회원가입 (GET = 페이지, POST = 처리)
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        user_id = request.POST.get("user_id")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "비밀번호가 일치하지 않습니다.")
            return redirect("register")

        if User.objects.filter(user_id=user_id).exists():
            messages.error(request, "이미 존재하는 아이디입니다.")
            return redirect("register")

        User.objects.create_user(user_id=user_id, username=username, password=password)
        messages.success(request, "회원가입 성공! 로그인 해주세요.")
        return redirect("login")

    # GET 요청이면 회원가입 화면 보여주기
    return render(request, "register.html")


# 로그인 (GET = 페이지, POST = 처리)
def login_view(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        password = request.POST.get("password")

        user = authenticate(request, user_id=user_id, password=password)

        if user is not None:
            login(request, user)
            messages.success(request,f'{user.username}님 로그인 성공!')
            return redirect("/")  # 메인 페이지로 이동
        else:
            messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")
            return redirect("login")

    return render(request, "login.html")

# 로그아웃
def logout_view(request):
    logout(request)
    return redirect("login")

@csrf_exempt  # fetch POST 요청 허용
def firebase_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        uid = data.get("uid")
        email = data.get("email")
        name = data.get("name")

        # 이미 가입된 유저 확인
        user, created = User.objects.get_or_create(user_id=uid, defaults={"username": name})
        login(request, user)  # Django 세션 로그인
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "fail"}, status=400)

def home(request):
    GOOGLE_API_KEY = settings.GOOGLE_API_KEY

    # 1) 사진 찾기 (정확도 향상: textsearch + 스코어링)
    def get_place_photo_url(cafe):
        name = (getattr(cafe, "crawled_store_name", None) or getattr(cafe, "public_store_name", None) or "").strip()
        addr = (getattr(cafe, "address", "") or "").strip()

        q = f"{name} {addr}".strip()
        params = {
            "query": q,
            "key": GOOGLE_API_KEY,
            "language": "ko",
            "region": "kr",
        }
        lat = getattr(cafe, "lat", None) or getattr(cafe, "lat_n", None)
        lng = getattr(cafe, "lng", None) or getattr(cafe, "long_w", None)
        if lat and lng:
            params.update({"location": f"{lat},{lng}", "radius": 1200})

        sr = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params, timeout=8
        ).json()
        results = sr.get("results", [])
        if not results:
            return None

        # 후보 스코어링
        def _dist_m(a_lat, a_lng, b_lat, b_lng):
            try:
                from math import radians, cos, sin, asin, sqrt
                R = 6371000.0
                dlat = radians(b_lat - a_lat)
                dlng = radians(b_lng - a_lng)
                aa = sin(dlat/2)**2 + cos(radians(a_lat))*cos(radians(b_lat))*sin(dlng/2)**2
                return 2*R*asin(sqrt(aa))
            except Exception:
                return None

        target_name = (name or "").lower()
        target_addr = addr
        best, best_score = None, -1
        for it in results:
            score = 0
            nm = (it.get("name") or "").lower()
            if target_name and target_name in nm:
                score += 3
            types = it.get("types", [])
            if "cafe" in types or "coffee_shop" in types:
                score += 3
            fa = it.get("formatted_address") or ""
            if target_addr and any(tok and tok in fa for tok in target_addr.split()[:3]):
                score += 2
            if lat and lng and it.get("geometry", {}).get("location"):
                p = it["geometry"]["location"]
                d = _dist_m(float(lat), float(lng), p.get("lat"), p.get("lng"))
                if d is not None:
                    if d <= 300: score += 3
                    elif d <= 1000: score += 1
            if score > best_score:
                best_score, best = score, it

        place_id = (best or {}).get("place_id")
        if not place_id:
            return None

        dr = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": place_id, "fields": "photos", "language": "ko", "key": GOOGLE_API_KEY},
            timeout=8
        ).json()
        photos = dr.get("result", {}).get("photos") or []
        if not photos:
            return None

        ref = photos[0].get("photo_reference")
        if not ref:
            return None
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=640&photo_reference={ref}&key={GOOGLE_API_KEY}"

    # 2) 키 생성(중복 판단용)
    def _norm(s: str) -> str:
        return " ".join((s or "").strip().lower().split())

    def _key(cafe):
        name = (getattr(cafe, "crawled_store_name", None) or getattr(cafe, "public_store_name", None) or "")
        addr = getattr(cafe, "address", "") or ""
        return (_norm(name), _norm(addr))

    # 3) 카테고리별 2개씩 뽑되, (이름+주소) 중복은 전체에서 제거
    flag_fields = [
        'comfy_cafe','solo_cafe','book_cafe','unique_cafe','group_cafe',
        'coffee_taste_cafe','study_cafe','bright_cafe','mood_cafe',
        'dessert_taste_cafe','cheap_cafe','animal_cafe','night_cafe','hanok_cafe',
    ]

    seen = set()
    picked = []  # 최종 추천 리스트

    for field in flag_fields:
        # 중복 제거 때문에 모자랄 수 있으니 넉넉히 후보 가져오고 그 안에서 2개 채우기
        candidates = list(
            DfCafeFull.objects.filter(**{field: 1}).order_by('?')[:60]
        )
        cat_bucket = []
        for c in candidates:
            k = _key(c)
            if k in seen:
                continue
            seen.add(k)
            cat_bucket.append(c)
            if len(cat_bucket) == 2:
                break
        picked.extend(cat_bucket)

    # 보기 좋게 섞기
    random.shuffle(picked)

    # 4) 사진 붙이기 (중복 API 호출 방지 캐시)
    photo_cache = {}
    for c in picked:
        k = _key(c)
        if k not in photo_cache:
            photo_cache[k] = get_place_photo_url(c)
        c.google_photo_url = photo_cache[k]
        nm = (getattr(c, "crawled_store_name", None) or getattr(c, "public_store_name", None) or "").strip()
        print(f"[GooglePhoto] {nm} -> {c.google_photo_url}")

    # 5) 렌더 (home.html이 include 'cafes/_cafe_cards.html' with cafes=recommend_cafes 사용)
    return render(request, "home.html", {"recommend_cafes": picked})