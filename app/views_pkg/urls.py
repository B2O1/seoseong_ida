from django.urls import path
from seoseong_ida.app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('posts/', views.posts_json, name='posts_json'),
    path('login/', views.login, name='login'), 
    path('search/', views.search, name='search'), 
    path('category/', views.category, name='category'), 
    path('menu/', views.menu, name='menu'), 
    path('register/', views.register, name='register'),
    path('findbymap/', views.findbymap, name='findbymap'),
]
