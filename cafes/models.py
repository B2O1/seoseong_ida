# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class DfCafeFull(models.Model):
    id = models.AutoField(primary_key=True)
    public_store_name = models.CharField(max_length=255, blank=True, null=True)
    crawled_store_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    visit_time = models.CharField(max_length=100, blank=True, null=True)
    rating = models.CharField(max_length=20, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    date = models.CharField(max_length=20, blank=True, null=True)
    revisit = models.IntegerField(blank=True, null=True)
    visit_purpose = models.CharField(max_length=255, blank=True, null=True)
    companion = models.CharField(max_length=100, blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    select_count = models.IntegerField(blank=True, null=True)
    facilities = models.CharField(max_length=255, blank=True, null=True)
    final_crawl_count = models.IntegerField(blank=True, null=True)
    total_review_count = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    comfy_cafe = models.IntegerField(blank=True, null=True)
    solo_cafe = models.IntegerField(blank=True, null=True)
    book_cafe = models.IntegerField(blank=True, null=True)
    unique_cafe = models.IntegerField(blank=True, null=True)
    group_cafe = models.IntegerField(blank=True, null=True)
    coffee_taste_cafe = models.IntegerField(blank=True, null=True)
    study_cafe = models.IntegerField(blank=True, null=True)
    bright_cafe = models.IntegerField(blank=True, null=True)
    mood_cafe = models.IntegerField(blank=True, null=True)
    dessert_taste_cafe = models.IntegerField(blank=True, null=True)
    cheap_cafe = models.IntegerField(blank=True, null=True)
    animal_cafe = models.IntegerField(blank=True, null=True)
    night_cafe = models.IntegerField(blank=True, null=True)
    hanok_cafe = models.IntegerField(blank=True, null=True)
    # google_place_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    # google_photo_id = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'df_cafe_full'

class CafePhotoCache(models.Model):
    key = models.CharField(max_length=255, unique=True, db_index=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    photo_ref = models.TextField(blank=True, null=True)                  
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
