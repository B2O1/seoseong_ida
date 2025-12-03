from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import MyUser, FaqPost

# ----- admin에서 쓸 폼들 -----
class MyUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ("user_id", "username", "email")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class MyUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label=("Password"),
        help_text=("Raw passwords are not stored, so there is no way to see "
                   "this user’s password, but you can change the password "
                   "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = MyUser
        fields = ("user_id", "username", "email", "password",
                  "is_active", "is_staff", "is_superuser", "groups", "user_permissions")

    def clean_password(self):
        # admin에서 비밀번호 해시를 그대로 유지
        return self.initial.get("password")


class MyUserAdmin(BaseUserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm

    list_display = ("user_id", "username", "email", "is_staff", "is_superuser")
    list_filter  = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("user_id", "username", "email")
    ordering = ("user_id",)

    fieldsets = (
        ("계정", {"fields": ("user_id", "username", "email", "password")}),
        ("권한", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("기타", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("user_id", "username", "email", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

admin.site.register(MyUser, MyUserAdmin)

# 참고: FAQ 모델도 admin에서 보이게
@admin.register(FaqPost)
class FaqPostAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "created_at", "has_answer")
    search_fields = ("name", "email", "question", "answer")
    list_filter = ("created_at",)
    def has_answer(self, obj): return bool(obj.answer)
    has_answer.boolean = True
