from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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
    email = models.EmailField(blank=True, null=True)  # 추가

    objects = MyUserManager()

    USERNAME_FIELD = 'user_id'     # 로그인할 때 사용할 필드
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    
class FaqPost(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    question = models.TextField()
    answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.created_at:%Y-%m-%d %H:%M}"
    
class FaqComment(models.Model):
    post = models.ForeignKey(FaqPost, on_delete=models.CASCADE, related_name="comments")
    author = models.CharField(max_length=50)
    content = models.TextField()
    is_staff = models.BooleanField(default=False)  # ✅ 관리자 여부 추가
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author}: {self.content[:20]}"