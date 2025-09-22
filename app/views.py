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

def posts_json(request):
    data = list(Post.objects.values('id', 'title', 'content', 'created_at').order_by('-id'))
    return JsonResponse(
        data,
        safe=False,
        json_dumps_params={'ensure_ascii': False, 'indent': 2, 'default': str},
        content_type='application/json; charset=utf-8'
    )
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