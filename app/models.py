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

    class Meta:
        managed = False               # 기존 테이블을 그대로 씀 (migrate로 만들지 않음)
        db_table = 'df_cafe_full'

    # 템플릿 호환 ({{ cafe.name }}, {{ cafe.description }})
    @property
    def name(self):
        return self.public_store_name or self.crawled_store_name or "(이름 없음)"

    @property
    def description(self):
        # 필요한 경우 content 일부를 요약해서 반환
        if self.content:
            return (self.content[:120] + "…") if len(self.content) > 120 else self.content
        return ""
