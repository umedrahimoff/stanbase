# stanbase

Платформа для компаний и инвесторов Центральной Азии.

## Структура проекта

```
stanbase/
├── main.py              # Основное приложение FastAPI
├── models.py            # SQLAlchemy модели
├── db.py                # Настройки базы данных
├── init_db.py           # Инициализация БД
├── requirements.txt     # Зависимости
├── Procfile             # Конфигурация для Heroku
├── services/            # Бизнес-логика
│   ├── api.py          # REST API роуты
│   ├── cache.py        # Система кеширования
│   ├── pagination.py   # Система пагинации
│   ├── comments.py     # Сервис комментариев
│   └── notifications.py # Сервис уведомлений
├── utils/               # Утилиты
│   ├── security.py     # Функции безопасности
│   ├── csrf.py         # CSRF защита
│   ├── migrate_passwords.py # Миграция паролей
│   └── migrate_to_prod.py  # Миграция для продакшена
├── tests/               # Тесты
│   ├── test_new_features.py
│   ├── test_performance.py
│   └── test_security.py
├── reports/             # Отчеты
│   ├── NEW_FEATURES_REPORT.md
│   └── SECURITY_UPGRADE_REPORT.md
├── docs/                # Документация
├── templates/           # Jinja2 шаблоны
├── static/              # Статические файлы
└── cache/               # Кеш файлы
```

## Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Инициализация БД
python3 init_db.py

# Запуск сервера
uvicorn main:app --reload
```

## Функции

- 🔐 Безопасность: хеширование паролей, JWT, CSRF защита
- 📧 Уведомления: система уведомлений для пользователей
- 💬 Комментарии: комментарии и ответы к записям
- 🚀 API: REST API для интеграции
- ⚡ Производительность: кеширование и пагинация
- 📊 Админка: управление контентом 