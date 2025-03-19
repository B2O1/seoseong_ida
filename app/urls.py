from django.urls import path
from app.views import views

urlpatterns = [
    path('', views.home, name='home')
]