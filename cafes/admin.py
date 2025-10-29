from django.contrib import admin
<<<<<<< HEAD
from .models import CafePhotoCache

@admin.register(CafePhotoCache)
class CafePhotoCacheAdmin(admin.ModelAdmin):
    list_display = ("key", "place_id", "photo_ref", "fetched_at")
    search_fields = ("key", "place_id", "photo_ref")
=======

# Register your models here.
>>>>>>> origin/hammm
