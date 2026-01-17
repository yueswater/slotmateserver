import os

# SMTP 郵件伺服器設定
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "sungpinyue@gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

if not EMAIL_HOST_PASSWORD:
    print("⚠️ 警告：未偵測到 EMAIL_HOST_PASSWORD 環境變數，郵件功能可能無法正常運作。")
