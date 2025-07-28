# Инструкции по настройке Stanbase

## 🚀 Быстрый старт

### 1. Клонирование и установка зависимостей
```bash
git clone <repository-url>
cd stanbase
pip install -r requirements.txt
```

### 2. Настройка окружения
```bash
# Скопируйте шаблон переменных окружения
cp env.example .env

# Отредактируйте .env файл с вашими настройками
# Особенно важно настроить:
# - SECRET_KEY (сгенерируйте новый)
# - SESSION_SECRET_KEY (сгенерируйте новый)
# - DATABASE_URL (если используете другую БД)
```

### 3. Инициализация базы данных
```bash
# Создайте базу данных и таблицы
python init_db.py

# Или запустите миграцию через API (если сервер запущен)
curl http://localhost:8000/run-migration
```

### 4. Запуск сервера
```bash
# Разработка
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Продакшн
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📧 Настройка почты (опционально)

### Для тестирования:
1. Создайте почтовый ящик на Beget.com
2. Обновите настройки в `.env`:
```env
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-password
MAIL_SERVER=smtp.beget.com
MAIL_PORT=465
MAIL_USE_SSL=True
```

### Для продакшна:
- Используйте реальные SMTP настройки
- Настройте `SITE_URL` на ваш домен
- Добавьте реальные email адреса администраторов

## 🔧 Возможные проблемы

### Ошибка "No module named 'migrate_to_prod'"
- ✅ Исправлено в последней версии
- Теперь используется встроенная миграция

### Ошибки подключения к базе данных
- Проверьте `DATABASE_URL` в `.env`
- Убедитесь, что база данных создана
- Запустите `python init_db.py`

### Ошибки отправки почты
- Проверьте настройки SMTP в `.env`
- Убедитесь, что порт не заблокирован
- Проверьте логи сервера

## 📁 Структура проекта

```
stanbase/
├── main.py              # Основное приложение
├── models.py            # Модели базы данных
├── db.py               # Настройки БД
├── init_db.py          # Инициализация БД
├── requirements.txt    # Зависимости Python
├── .env               # Переменные окружения (не в git)
├── env.example        # Шаблон переменных окружения
├── static/            # Статические файлы
├── templates/         # HTML шаблоны
├── services/          # Бизнес-логика
├── utils/             # Утилиты
└── instance/          # База данных SQLite
```

## 🛠️ Разработка

### Добавление новых функций:
1. Создайте модель в `models.py`
2. Добавьте эндпоинты в `main.py`
3. Создайте шаблоны в `templates/`
4. Добавьте стили в `static/`

### Тестирование:
```bash
# Запустите сервер
uvicorn main:app --reload

# Откройте в браузере
http://localhost:8000
```

## 📝 Полезные команды

```bash
# Проверка статуса БД
curl http://localhost:8000/test-db

# Запуск миграции
curl http://localhost:8000/run-migration

# Очистка кэша Python
find . -type d -name "__pycache__" -exec rm -r {} +
```

## 🔒 Безопасность

- Никогда не коммитьте файл `.env`
- Используйте сильные SECRET_KEY
- Настройте HTTPS для продакшна
- Регулярно обновляйте зависимости

---
*Обновлено: $(date)* 