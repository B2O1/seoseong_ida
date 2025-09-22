from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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


class MyUserManager(BaseUserManager):
    def create_user(self, user_id, username, password=None):
        if not user_id:
            raise ValueError("아이디는 반드시 입력해야 합니다.")
        user = self.model(user_id=user_id, username=username)
        user.set_password(password)  # 비밀번호 해시화
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, username, password):
        user = self.create_user(user_id=user_id, username=username, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=20, unique=True)
    username = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'user_id'     # 로그인할 때 사용할 필드
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username