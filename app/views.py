import json
import random
import requests
import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import (
    Exists, OuterRef, FloatField, Q, F, Window, CharField, IntegerField
)
from django.db.models.functions import Cast, RowNumber
from django.db.models.expressions import Func, Value
from cafes.models import DfCafeFull, CafePhotoCache
from .models import FaqPost, FaqComment
from django import forms
from django.core.paginator import Paginator


class FaqAnswerForm(forms.ModelForm):
    class Meta:
        model = FaqPost
        fields = ['answer']

@staff_member_required
def faq_answer(request, pk):
    item = get_object_or_404(FaqPost, pk=pk)
    form = FaqAnswerForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("faq_detail", pk=pk)
    return render(request, "faq-answer.html", {"item": item, "form": form})
class FaqCommentForm(forms.ModelForm):
    class Meta:
        model = FaqComment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, "placeholder": "댓글을 입력하세요"}),
        }

def faq_detail(request, pk):
    item = get_object_or_404(FaqPost, pk=pk)
    comments = item.comments.all()

    if request.user.is_authenticated:
        if request.method == "POST" and request.POST.get("form_type") == "comment":
            cform = FaqCommentForm(request.POST)
            if cform.is_valid():
                comment = cform.save(commit=False)
                comment.post = item
                comment.author = request.user.username
                comment.is_staff = request.user.is_staff  # ✅ 여기서 자동 기록
                comment.save()
                return redirect("faq_detail", pk=item.pk)
        else:
            cform = FaqCommentForm()
    else:
        cform = None

    return render(request, "faq-detail.html", {
        "item": item,
        "comments": comments,
        "cform": cform,
    })

# (선택) 관리자만 댓글 삭제
@staff_member_required
def faq_comment_delete(request, cid):
    comment = get_object_or_404(FaqComment, pk=cid)
    post_id = comment.post_id
    comment.delete()
    return redirect("faq_detail", pk=post_id)

class FaqForm(forms.ModelForm):
    class Meta:
        model = FaqPost
        fields = ['name', 'email', 'question']


def faq_list(request):
    items = FaqPost.objects.all().order_by('-created_at')

    processed = []

    for obj in items:
        q = obj.question or ""
        q_type = "기타"      # 기본값
        body = q

        # ============================
        # 🔍 [문의 유형: XXX] 형식 파싱
        # ============================
        if q.startswith("[문의 유형:"):
            end = q.find("]")
            if end != -1:
                header = q[: end + 1]  # "[문의 유형: XXX]"
                # "XXX" 부분만 추출
                q_type = header.replace("[문의 유형:", "").replace("]", "").strip()
                # 본문(body)에서 유형 부분 제거
                body = q[end + 1:].lstrip("\n")

        # ============================
        # 🔍 제목 = 본문 첫 줄
        # ============================
        lines = body.splitlines()
        title = lines[0] if lines else ""

        # ============================
        # 🔍 템플릿에서 사용할 임시 필드
        # ============================
        obj.display_type = q_type
        obj.display_title = title
        obj.display_body = body

        processed.append(obj)

    # ============================
    # 🔍 페이지네이션 (기존 코드 그대로)
    # ============================
    paginator = Paginator(processed, 3)  # 페이지당 3개 (네 코드 그대로)
    page = request.GET.get('page')
    items_page = paginator.get_page(page)

    return render(request, 'faq.html', {
        'items': items_page
    })

def _display_name_from_session_or_user(request):
    # 세션에 우리가 넣어둔 표시명(없는 경우 username)
    return (request.session.get("display_name")
            or getattr(request.user, "username", "")
            or "")

@login_required
def faq_write(request):
    if request.method == "POST":
        form = FaqForm(request.POST)

        # 로그인 상태라면 name/email은 사용자가 뭘 보내든 서버에서 덮어씀
        if request.user.is_authenticated:
            # 폼 유효성 때문에 required 완화
            if "name" in form.fields:
                form.fields["name"].required = False
            if "email" in form.fields:
                form.fields["email"].required = False

        if form.is_valid():
            obj = form.save(commit=False)

            if request.user.is_authenticated:
                obj.email = (getattr(request.user, "email", "") or "")
                obj.name  = _display_name_from_session_or_user(request)
                # 익명 사용자 우회 방지로 여기서 강제 세팅 (폼 값 무시)
            else:
                # 비로그인 사용자는 폼 입력 그대로 사용
                pass

            obj.save()
            messages.success(request, "문의가 등록되었습니다.")
            return redirect("faq_list")
    else:
        # GET 폼 준비
        form = FaqForm()
        if request.user.is_authenticated:
            # 화면에서는 숨길 거지만, 혹시 폼이 필수로 되어 있으면 HiddenInput으로 처리
            if "name" in form.fields:
                form.fields["name"].widget = forms.HiddenInput()
                form.fields["name"].required = False
                form.initial["name"] = _display_name_from_session_or_user(request)
            if "email" in form.fields:
                form.fields["email"].widget = forms.HiddenInput()
                form.fields["email"].required = False
                form.initial["email"] = getattr(request.user, "email", "")
    return render(request, "faq-write.html", {"form": form})


# ----------------------------
# Google Place Photo helpers
# ----------------------------
def _norm_key(name: str, address: str) -> str:
    n = " ".join((name or "").strip().lower().split())
    a = " ".join((address or "").strip().lower().split())
    return f"{n} | {a}"

def _fetch_place_photo_ref(cafe, GOOGLE_API_KEY):
    """TextSearch → 후보 스코어링 → Details 로 첫 번째 photo_reference 반환"""
    name = (getattr(cafe, "crawled_store_name", None)
            or getattr(cafe, "public_store_name", None)
            or "").strip()
    addr = (getattr(cafe, "address", "") or "").strip()
    q = f"{name} {addr}".strip()

    params = {"query": q, "key": GOOGLE_API_KEY, "language": "ko", "region": "kr"}
    lat = getattr(cafe, "lat", None) or getattr(cafe, "lat_n", None)
    lng = getattr(cafe, "lng", None) or getattr(cafe, "long_w", None)
    if lat and lng:
        params.update({"location": f"{lat},{lng}", "radius": 1200})

    sr = requests.get(
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        params=params,
        timeout=8
    ).json()

    print("TEXTSEARCH status:", sr.get("status"), sr.get("error_message"))
    print("TEXTSEARCH results:", len(sr.get("results", [])))

    results = sr.get("results", [])
    if not results:
        return None, None, None, None

    def _dist(a_lat, a_lng, b_lat, b_lng):
        from math import radians, cos, sin, asin, sqrt
        try:
            R = 6371000.0
            dlat = radians(b_lat - a_lat)
            dlng = radians(b_lng - a_lng)
            aa = (sin(dlat / 2) ** 2
                  + cos(radians(a_lat)) * cos(radians(b_lat))
                  * sin(dlng / 2) ** 2)
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

    dr = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json",
        params={
            "place_id": place_id,
            "fields": "photos",
            "language": "ko",
            "key": GOOGLE_API_KEY
        },
        timeout=8
    ).json()

    print("DETAILS status:", dr.get("status"), dr.get("error_message"))
    print("DETAILS photos:", len((dr.get("result", {}).get("photos") or [])))

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

def _get_cached_photo_url_only(cafe, GOOGLE_API_KEY):
    name = (getattr(cafe, "crawled_store_name", None) or getattr(cafe, "public_store_name", None) or "").strip()
    address = (getattr(cafe, "address", "") or "").strip()
    key = _norm_key(name, address)

    cache = CafePhotoCache.objects.filter(key=key).only("photo_ref").first()
    if cache and cache.photo_ref:
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=640&photo_reference={cache.photo_ref}&key={GOOGLE_API_KEY}"
    return None

# 2) home()에서 캐시만 확인하도록 루프만 교체
def home(request):
    GOOGLE_API_KEY = settings.GOOGLE_API_KEY
    flag_fields = [
        'comfy_cafe', 'solo_cafe', 'book_cafe', 'unique_cafe', 'group_cafe',
        'coffee_taste_cafe', 'study_cafe', 'bright_cafe', 'mood_cafe',
        'dessert_taste_cafe', 'cheap_cafe', 'animal_cafe', 'night_cafe', 'hanok_cafe',
    ]

    all_recommended = []
    for field in flag_fields:
        cafes = DfCafeFull.objects.filter(**{field: 1}).order_by('?')[:2]
        all_recommended.extend(cafes)

    random.shuffle(all_recommended)

    # ✅ 캐시만 확인 (느린 외부 호출 금지)
    for c in all_recommended:
        c.google_photo_url = _get_cached_photo_url_only(c, GOOGLE_API_KEY)

    return render(request, "home.html", {"recommend_cafes": all_recommended})

# 3) 클라이언트가 나중에 사진 요청하는 API
@require_GET
def cafe_photo_api(request, cafe_id):
    # print("KEY:", settings.GOOGLE_API_KEY)
    cafe = get_object_or_404(DfCafeFull, pk=cafe_id)
    # 캐시 미스일 때만 내부에서 Google 호출 (이미 너의 파일에 있는 함수 재사용)
    url = get_place_photo_url_with_cache(cafe, settings.GOOGLE_API_KEY)
    return JsonResponse({"url": url})

def search(request):
    return render(request, "search.html")
def mypage(request):
    return render(request, "mypage.html")

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

# 로그인 페이지 렌더
def login_page(request):
    return render(request, 'login.html', {
        'firebase_config': settings.FIREBASE_CONFIG
    })

def _email_local_for_display(email: str) -> str:
    if not email:
        return ""
    local, _, domain = email.partition("@")
    local = local.split("+", 1)[0]
    if domain.lower() in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
    return local or ""

@csrf_exempt
def firebase_login(request):
    if request.method == "POST":
        # 🔹 1. 요청 본문(raw body) 확인
        print("📩 [firebase_login] Raw request body:", request.body)

        # 🔹 2. JSON 디코딩 시도
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError as e:
            print("❌ JSON 파싱 실패:", e)
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        # 🔹 3. idToken 추출
        id_token = body.get("idToken")
        print("🔥 [firebase_login] idToken:", id_token)

        if not id_token:
            return JsonResponse({"error": "idToken not provided"}, status=400)

        try:
            # 🔹 4. Firebase 토큰 검증
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")
            print(f"✅ Firebase 인증 성공: uid={uid}, email={email}")

            # 🔹 5. Django 유저 생성 or 가져오기 (이메일 우선 매핑)
            from django.contrib.auth import get_user_model, login
            User = get_user_model()

            # 이메일이 없을 수도 있는 공급자 대비
            if not email:
                email = f"{uid}@autogen.firebase"
                print(f"ℹ️ email이 없어 임시 이메일 사용: {email}")

            # 5-1) 이메일로 기존 유저 우선 탐색
            user = User.objects.filter(email__iexact=email).first() if email else None
            if not user and uid:
                user = User.objects.filter(user_id=uid).first()

            if not user:
                local_part = (email.split("@", 1)[0] if email else uid) or uid
                username = local_part[:24]

                user = User.objects.create_user(
                    user_id=uid,       # ← 길이 늘리면 그대로 저장 가능
                    username=username,
                    password=None,
                )
                if email:
                    user.email = email
                    user.save(update_fields=["email"])
                print(f"🆕 새 사용자 생성: username={user.username}, email={user.email}")
            else:
                print(f"🔁 기존 사용자 로그인: username={user.username}, email={user.email}")
            display_name = _email_local_for_display(email)
            request.session["display_name"] = display_name
            # 🔹 6. Django 세션 로그인 처리 (그대로 유지)
            login(request, user)
            print("🎉 Django 세션 로그인 완료:", user.username)

            # 🔹 응답 형태도 그대로 유지 (최소 변경)
            return JsonResponse({"status": "success"})
        except Exception as e:
            print("🚨 Firebase 인증 에러:", e)
            return JsonResponse({"error": str(e)}, status=400)

    # 🔹 GET 또는 다른 메서드일 경우 (그대로 유지)
    return JsonResponse({"error": "POST method required"}, status=405)


def firebase_config_view(request):
    return JsonResponse(settings.FIREBASE_CONFIG)

@csrf_exempt
def firebase_logout(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    logout(request)  # Django 세션 종료
    return JsonResponse({"ok": True})


# cafes/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .agent import run_cafe_agent   # 아까 만든 함수


def chatbot_view(request):
    """챗봇 페이지 렌더링"""
    return render(request, "chatbot.html")


@csrf_exempt  # 개발용: 편하게 먼저 이렇게, 나중에 CSRF 처리 정교하게 해도 됨
def chatbot_api(request):
    """AJAX로 질문을 받아서 에이전트 실행 후 JSON 응답"""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_message = data.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "message is required"}, status=400)

    result = run_cafe_agent(user_message)

    return JsonResponse(
        {
            "answer": result["answer"],
            "sql": result["sql"],
            "error": result["error"],
            # 필요하면 raw_results도 내려줄 수 있음
            # "raw_results": result["raw_results"],
        }
    )

