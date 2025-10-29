from django.contrib import admin
from .models import CafePhotoCache

@admin.register(CafePhotoCache)
class CafePhotoCacheAdmin(admin.ModelAdmin):
    list_display = ("key", "place_id", "photo_ref", "fetched_at")
    search_fields = ("key", "place_id", "photo_ref")
