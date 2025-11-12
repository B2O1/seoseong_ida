from django.apps import AppConfig


class MainscreenConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

# class AppConfigWithFirebase(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "app"

#     def ready(self):
#         # Firebase Admin 초기화 (한 번만)
#         import os
#         import firebase_admin
#         from firebase_admin import credentials
#         from django.conf import settings

#         if not firebase_admin._apps:
#             cred_path = getattr(settings, "FIREBASE_CREDENTIAL_PATH", None)
#             if not cred_path or not os.path.exists(cred_path):
#                 # 키 파일이 없으면 초기화 생략(로컬/테스트 대비)
#                 return
#             cred = credentials.Certificate(cred_path)
#             firebase_admin.initialize_app(cred)