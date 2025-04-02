from django.urls import path
from app.views import views

urlpatterns = [
    path('', views.home, name='home'),  path('login/', views.login, name='login'), path('search/', views.search, name='search'), path('category/', views.category, name='category'), path('menu/', views.menu, name='menu'), path('register/', views.register, name='register')
]