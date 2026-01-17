from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),  # Access Token 活 60 分鐘
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # Refresh Token 活 1 天
}
