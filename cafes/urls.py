from django.urls import path
from .views import FindByMapView, cafes_api

urlpatterns = [
    path("findbymap/", FindByMapView.as_view(), name="findbymap"),
    path("api/", cafes_api, name="cafes_api"),
]