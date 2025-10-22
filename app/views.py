from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from cafes.models import DfCafeFull, CafePhotoCache
from django.db.models import (
    Exists, OuterRef, FloatField, Q,
    F, Window, CharField, IntegerField
)
from django.db.models.functions import Cast, RowNumber
from django.db.models.expressions import Func, Value

import json
import random
import requests


# ----------------------------
# Google Place Photo helpers
# ----------------------------
def _norm_key(name: str, address: str) -> str:
    n = " ".join((name or "").strip().lower().split())
    a = " ".join((address or "").strip().lower().split())
    return f"{n} | {a}"


def _fetch_place_photo_ref(cafe, GOOGLE_API_KEY):
    """TextSearch → 후보 스코어링 → Details 로 첫 번째 photo_reference 반환"""
    name = (getattr(cafe, "crawled_store_name", None) or getattr(cafe, "public_store_name", None) or "").strip()
    addr = (getattr(cafe, "address", "") or "").strip()
    q = f"{name} {addr}".strip()

    params = {"query": q, "key": GOOGLE_API_KEY, "language": "ko", "region": "kr"}
    lat = getattr(cafe, "lat", None) or getattr(cafe, "lat_n", None)
    lng = getattr(cafe, "lng", None) or getattr(cafe, "long_w", None)
    if lat and lng:
        params.update({"location": f"{lat},{lng}", "radius": 1200})

    sr = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json",
                      params=params, timeout=8).json()
    results = sr.get("results", [])
    if not results:
        return None, None, None, None

    def _dist(a_lat, a_lng, b_lat, b_lng):
        from math import radians, cos, sin, asin, sqrt
        try:
            R = 6371000.0
            dlat = radians(b_lat - a_lat)
            dlng = radians(b_lng - a_lng)
            aa = sin(dlat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(dlng / 2) ** 2
            return 2 * R * asin(sqrt(aa))
        except Exception:
            return None

    tname = name.lower()
    best, best_score = None, -1
    for it in results:
        score = 0
        nm = (it.get("name") or "").lower()
        if tname and tname in nm:
            score += 3
        types = it.get("types", [])
        if "cafe" in types or "coffee_shop" in types:
            score += 3
        if lat and lng and it.get("geometry", {}).get("location"):
            p = it["geometry"]["location"]
            d = _dist(float(lat), float(lng), p.get("lat"), p.get("lng"))
            if d is not None:
                if d <= 300:
                    score += 3
                elif d <= 1000:
                    score += 1
        if score > best_score:
            best_score, best = score, it

    place_id = (best or {}).get("place_id")
    if not place_id:
        return None, None, None, None

    dr = requests.get("https://maps.googleapis.com/maps/api/place/details/json",
                      params={"place_id": place_id, "fields": "photos",
                              "language": "ko", "key": GOOGLE_API_KEY},
                      timeout=8).json()
    photos = dr.get("result", {}).get("photos") or []
    if not photos:
        return place_id, None, None, None

    ph = photos[0]
    return place_id, ph.get("photo_reference"), ph.get("width"), ph.get("height")


def get_place_photo_url_with_cache(cafe, GOOGLE_API_KEY):
    name = (getattr(cafe, "crawled_store_name", None) or getattr(cafe, "public_store_name", None) or "").strip()
    address = (getattr(cafe, "address", "") or "").strip()
    key = _norm_key(name, address)

    cache = CafePhotoCache.objects.filter(key=key).first()
    if cache and cache.photo_ref:
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=640&photo_reference={cache.photo_ref}&key={GOOGLE_API_KEY}"

    place_id, photo_ref, w, h = _fetch_place_photo_ref(cafe, GOOGLE_API_KEY)
    CafePhotoCache.objects.update_or_create(
        key=key,
        defaults={
            "place_id": place_id or None,
            "photo_ref": photo_ref,
            "width": w,
            "height": h,
        },
    )

    return (
        f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=640&photo_reference={photo_ref}&key={GOOGLE_API_KEY}"
        if photo_ref else None
    )


# ----------------------------
# Views
# ----------------------------
def home(request):
    GOOGLE_API_KEY = settings.GOOGLE_API_KEY
    flag_fields = [
        'comfy_cafe', 'solo_cafe', 'book_cafe', 'unique_cafe', 'group_cafe',
        'coffee_taste_cafe', 'study_cafe', 'bright_cafe', 'mood_cafe',
        'dessert_taste_cafe', 'cheap_cafe', 'animal_cafe', 'night_cafe', 'hanok_cafe',
    ]

    all_recommended = []
    for field in flag_fields:
        cafes = DfCafeFull.objects.filter(**{field: 1}).order_by('?')[:1]
        all_recommended.extend(cafes)

    random.shuffle(all_recommended)
    for c in all_recommended:
        c.google_photo_url = get_place_photo_url_with_cache(c, GOOGLE_API_KEY)

    return render(request, "home.html", {"recommend_cafes": all_recommended})


def search(request):
    return render(request, "search.html")


User = get_user_model()


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

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        password = request.POST.get("password")

        user = authenticate(request, user_id=user_id, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"{user.username}님 로그인 성공!")
            return redirect("/")
        else:
            messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")
            return redirect("login")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@csrf_exempt
def firebase_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        uid = data.get("uid")
        email = data.get("email")
        name = data.get("name")

        user, created = User.objects.get_or_create(user_id=uid, defaults={"username": name})
        login(request, user)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "fail"}, status=400)