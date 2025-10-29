from django.urls import path
from .views import FindByMapView, cafes_api, CategoryView

urlpatterns = [
    path("findbymap/", FindByMapView.as_view(), name="findbymap"),
    path("category/", CategoryView.as_view(), name="category"),
    path("api/", cafes_api, name="cafes_api"),
]