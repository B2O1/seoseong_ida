from django.shortcuts import render

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
def findbymap_2(request):
    return render(request, 'findbymap_2.html')