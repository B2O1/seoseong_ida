from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path("register/", views.register, name="register"),  # 회원가입
    path("login/", views.login_view, name="login"),      # 로그인
    path("logout/", views.logout_view, name="logout"),   # 로그아웃
    path('mypage/',views.mypage, name='mypage'), # 마이페이지로
    path('firebase/login/', views.firebase_login, name='firebase_login'),
    path("firebase/logout/", views.firebase_logout, name="firebase_logout"),
    path("api/cafes/<int:cafe_id>/photo/", views.cafe_photo_api, name="cafe_photo_api"),
    path('login/firebase/',views.firebase_config_view, name = 'firebase_login_view'),
    path("faq/", views.faq_list, name="faq_list"),           # 목록
    path("faq/write/", views.faq_write, name="faq_write"),   # 작성 (faq-write.html)
    path("faq/<int:pk>/", views.faq_detail, name="faq_detail"),  # ← 상세 보기
    path("faq/<int:pk>/answer/", views.faq_answer, name="faq_answer"),
    path("faq/comment/<int:cid>/delete/", views.faq_comment_delete, name="faq_comment_delete"),
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("chatbot/api/", views.chatbot_api, name="chatbot_api"),
]