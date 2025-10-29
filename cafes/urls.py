from django.urls import path
from .views import FindByMapView, cafes_api, CategoryView
<<<<<<< HEAD
from .views import place_photo_redirect
=======
>>>>>>> origin/hammm

urlpatterns = [
    path("findbymap/", FindByMapView.as_view(), name="findbymap"),
    path("category/", CategoryView.as_view(), name="category"),
    path("api/", cafes_api, name="cafes_api"),
<<<<<<< HEAD
    path("photo/<str:place_id>/<str:photo_id>/", place_photo_redirect, name="place_photo"),
=======
>>>>>>> origin/hammm
]