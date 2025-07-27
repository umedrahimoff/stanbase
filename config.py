"""
Конфигурация приложения
"""

import os

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8350354186:AAGPNR44pg4L0qHgpO8RAJRDoylKHlSFBak"
TELEGRAM_CHAT_ID = "-4753525145"

# Database Configuration
DATABASE_URL = "sqlite:///./instance/stanbase.db"

# Security Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Приоритет переменных окружения
def get_config(key, default=None):
    """Получить значение конфигурации с приоритетом переменных окружения"""
    return os.getenv(key, globals().get(key, default))

# Обновляем глобальные переменные
TELEGRAM_BOT_TOKEN = get_config("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
TELEGRAM_CHAT_ID = get_config("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
DATABASE_URL = get_config("DATABASE_URL", DATABASE_URL)
SECRET_KEY = get_config("SECRET_KEY", SECRET_KEY) 