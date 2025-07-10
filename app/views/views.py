from django.shortcuts import render
from app.models import Place

# Create your views here.
def home(request):
    return render(request, 'home.html')
def login(request):
    return render(request, 'login.html')
def register(request):
    return render(request, 'register.html')
def search(request):
    return render(request, 'search.html')
def category(request):
    return render(request, 'category.html')
def menu(request):
    return render(request, 'menu.html')
def findbymap(request):
    places = Place.objects.all()[:20]
    return render(request, 'findbymap.html', {
        'places': places,
    })
