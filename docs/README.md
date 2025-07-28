# Stanbase - Документация

База данных стартапов и инвесторов Центральной Азии

## 📋 Содержание

- [Обзор проекта](./overview.md)
- [Архитектура](./architecture.md)
- [API](./api.md)
- [База данных](./database.md)
- [Развертывание](./deployment.md)
- [Разработка](./development.md)
- [SEO и мета-теги](./seo.md)

## 🚀 Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Инициализация базы данных
python init_db.py

# Запуск приложения
python main.py
```

## 📁 Структура проекта

```
stanbase/
├── main.py              # Основное приложение FastAPI
├── models.py            # Модели SQLAlchemy
├── db.py               # Настройки базы данных
├── init_db.py          # Инициализация БД и тестовых данных
├── migrate_to_prod.py  # Миграции для продакшена
├── requirements.txt    # Зависимости Python
├── Procfile           # Конфигурация для Render
├── templates/         # Jinja2 шаблоны
├── static/           # Статические файлы
└── docs/            # Документация
```

## 🔧 Технологии

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** Jinja2, Bootstrap 5
- **Deployment:** Render
- **Database:** PostgreSQL (prod), SQLite (dev) 