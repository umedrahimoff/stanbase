"""
Конфигурация приложения
"""

import os

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_STAGING = ENVIRONMENT == "staging"

# Telegram Bot Configuration
# ⚠️ ВНИМАНИЕ: В продакшене используйте переменные окружения!
# Для разработки можно использовать токены здесь, но НЕ коммитьте их в Git
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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