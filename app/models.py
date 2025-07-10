from django.db import models

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

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