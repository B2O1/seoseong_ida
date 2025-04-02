
from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'menu-search-page.html')

def test_login(request) : 
    return render(request, 'test_login.html')

# def search_view(request) : 
#     return render(request, 'test_search.html')