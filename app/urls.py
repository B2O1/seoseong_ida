from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path("register/", views.register, name="register"),  # 회원가입
    path("login/", views.login_view, name="login"),      # 로그인
    path("logout/", views.logout_view, name="logout"),   # 로그아웃
    path('firebase/login/', views.firebase_login, name='firebase_login'),
    # path('posts/', views.posts_json, name='posts_json'),
    path("api/cafes/<int:cafe_id>/photo/", views.cafe_photo_api, name="cafe_photo_api"),
]