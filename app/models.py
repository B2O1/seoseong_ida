from django.db import models

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Cafe(models.Model):
    public_store_name  = models.CharField(max_length=255, blank=True, null=True)
    crawled_store_name = models.CharField(max_length=255, blank=True, null=True)
    category           = models.CharField(max_length=50, blank=True, null=True)
    visit_time         = models.CharField(max_length=100, blank=True, null=True)
    rating             = models.CharField(max_length=20, blank=True, null=True)  # 원본이 문자열이라 그대로
    source             = models.CharField(max_length=50, blank=True, null=True)
    content            = models.TextField(blank=True, null=True)
    date               = models.CharField(max_length=20, blank=True, null=True)
    revisit            = models.IntegerField(blank=True, null=True)
    visit_purpose      = models.CharField(max_length=255, blank=True, null=True)
    companion          = models.CharField(max_length=100, blank=True, null=True)
    tags               = models.CharField(max_length=255, blank=True, null=True)
    select_count       = models.IntegerField(blank=True, null=True)
    facilities         = models.CharField(max_length=255, blank=True, null=True)
    final_crawl_count  = models.IntegerField(blank=True, null=True)
    total_review_count = models.IntegerField(blank=True, null=True)
    address            = models.CharField(max_length=255, blank=True, null=True)

    # 필터용 Boolean/TINYINT(0/1)
    comfy_cafe         = models.IntegerField(blank=True, null=True)
    solo_cafe          = models.IntegerField(blank=True, null=True)
    book_cafe          = models.IntegerField(blank=True, null=True)
    unique_cafe        = models.IntegerField(blank=True, null=True)
    group_cafe         = models.IntegerField(blank=True, null=True)
    coffee_taste_cafe  = models.IntegerField(blank=True, null=True)
    study_cafe         = models.IntegerField(blank=True, null=True)
    bright_cafe        = models.IntegerField(blank=True, null=True)
    mood_cafe          = models.IntegerField(blank=True, null=True)
    dessert_taste_cafe = models.IntegerField(blank=True, null=True)
    cheap_cafe         = models.IntegerField(blank=True, null=True)
    animal_cafe        = models.IntegerField(blank=True, null=True)
    night_cafe         = models.IntegerField(blank=True, null=True)
    hanok_cafe         = models.IntegerField(blank=True, null=True)

from django.db import models

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class Place(models.Model):
    crawling_name   = models.CharField(
        max_length=255,
        db_column='크롤링 가게명',
        default='',
        blank=True
    )
    category        = models.CharField(
        max_length=100,
        db_column='카테고리',
        default='',
        blank=True
    )
    time            = models.CharField(
        max_length=100,
        db_column='시간',
        default='',
        blank=True
    )
    # rating을 문자열로 받도록 변경
    rating          = models.CharField(
        max_length=50,
        db_column='평점',
        default='',
        blank=True
    )
    source          = models.CharField(
        max_length=100,
        db_column='출처',
        default='',
        blank=True
    )
    content         = models.TextField(
        db_column='content',
        default='',
        blank=True
    )
    date            = models.CharField(
        max_length=50,
        db_column='date',
        default='',
        blank=True
    )
    revisit         = models.CharField(
        max_length=50,
        db_column='revisit',
        default='',
        blank=True
    )
    purpose         = models.CharField(
        max_length=100,
        db_column='방문목적',
        default='',
        blank=True
    )
    companion       = models.CharField(
        max_length=100,
        db_column='동반자',
        null=True,
        blank=True
    )
    tags            = models.CharField(
        max_length=255,
        db_column='태그',
        default='',
        blank=True
    )
    selection_count = models.IntegerField(
        db_column='선택 수',
        default=0
    )
    convenience     = models.CharField(
        max_length=255,
        db_column='편의시설',
        default='',
        blank=True
    )

    def __str__(self):
        return f"{self.crawling_name} ({self.category})"