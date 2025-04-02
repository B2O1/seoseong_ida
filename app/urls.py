from django.urls import path
from app.views import views

urlpatterns = [
    # 페이지 렌더링
    path('', views.home, name = 'home'),
    path('test_login/', views.test_login, name='test_login'),
]