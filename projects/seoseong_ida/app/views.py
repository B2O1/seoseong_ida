from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import firebase_admin
from firebase_admin import auth, credentials

# def posts_json(request):
#     data = list(Post.objects.values('id', 'title', 'content', 'created_at').order_by('-id'))
#     return JsonResponse(
#         data,
#         safe=False,
#         json_dumps_params={'ensure_ascii': False, 'indent': 2, 'default': str},
#         content_type='application/json; charset=utf-8'
#     )

# Create your views here.
def home(request):
    return render(request, 'home.html')
def search(request):
    return render(request, 'search.html')

User = get_user_model()

# Create your views here.
def home(request):
    return render(request, 'home.html')
def search(request):
    return render(request, 'search.html')
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

# 로그인 페이지 렌더
def login_page(request):
    return render(request, 'login.html', {
        'firebase_config': settings.FIREBASE_CONFIG
    })


# @csrf_exempt
# def firebase_login(request):
#     if request.method == "POST":
#         print("📩 request.body:", request.body)  # ✅ 추가
#         body = json.loads(request.body)
#         id_token = body.get("idToken")

#         try:
#             # 1. Firebase 토큰 검증
#             decoded_token = auth.verify_id_token(id_token)
#             uid = decoded_token["uid"]
#             email = decoded_token.get("email")

#             # 2. Django 유저 생성 or 불러오기
#             user, created = User.objects.get_or_create(
#                 username=uid,
#                 defaults={"email": email}
#             )

#             # 3. 세션 로그인
#             login(request, user)

#             return JsonResponse({"status": "success"})
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)

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

            # 🔹 5. Django 유저 생성 or 가져오기
            from django.contrib.auth import get_user_model, login
            User = get_user_model()

            user, created = User.objects.get_or_create(
                username=uid,
                defaults={"email": email or ""}
            )

            # 🔹 6. Django 세션 로그인 처리
            login(request, user)
            print("🎉 Django 세션 로그인 완료:", user.username)

            return JsonResponse({"status": "success"})
        except Exception as e:
            print("🚨 Firebase 인증 에러:", e)
            return JsonResponse({"error": str(e)}, status=400)

    # 🔹 GET 또는 다른 메서드일 경우
    return JsonResponse({"error": "POST method required"}, status=405)        

def firebase_config_view(request):
    return JsonResponse(settings.FIREBASE_CONFIG)

