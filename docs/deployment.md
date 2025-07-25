# Развертывание

## Обзор

Stanbase развертывается на платформе Render с использованием PostgreSQL в качестве базы данных.

## Платформа

### Render
- **Тип сервиса:** Web Service
- **Среда выполнения:** Python 3.9+
- **База данных:** PostgreSQL
- **Домен:** https://stanbasetech.onrender.com

## Конфигурация

### Procfile
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
jinja2==3.1.2
python-multipart==0.0.6
psycopg2-binary==2.9.9
requests==2.31.0
```

### Переменные окружения

#### Обязательные
```bash
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-here
```

#### Опциональные
```bash
DEBUG=False
ENVIRONMENT=production
```

## Процесс развертывания

### 1. Подготовка кода

```bash
# Проверка синтаксиса
python3 -m py_compile main.py

# Проверка зависимостей
pip install -r requirements.txt

# Тестирование локально
python main.py
```

### 2. Настройка Render

#### Создание Web Service
1. Подключение GitHub репозитория
2. Выбор Python runtime
3. Настройка build command: `pip install -r requirements.txt`
4. Настройка start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Создание PostgreSQL Database
1. Создание новой PostgreSQL базы данных
2. Копирование DATABASE_URL
3. Добавление переменной окружения в Web Service

### 3. Миграции базы данных

#### Автоматические миграции
```python
# migrate_to_prod.py
def migrate_production_database():
    # Проверка существования таблиц
    # Создание недостающих таблиц
    # Добавление недостающих колонок
    # Обновление данных
```

#### Выполнение миграций
```bash
# Через API эндпоинт
curl https://stanbasetech.onrender.com/run-migration
```

### 4. Импорт данных

#### Экспорт локальных данных
```python
# Создание JSON файла с данными
def export_data():
    # Экспорт всех таблиц
    # Сохранение в файл
```

#### Импорт на сервер
```python
# Отправка данных на сервер
def upload_data():
    # Чтение JSON файла
    # Отправка POST запроса
    # Проверка результата
```

## Мониторинг

### Логи приложения
- **Render Dashboard** → Logs
- **Время отклика** → Metrics
- **Ошибки** → Error tracking

### Состояние базы данных
```bash
# Проверка состояния БД
curl https://stanbasetech.onrender.com/test-db
```

### Проверка эндпоинтов
```bash
# Главная страница
curl https://stanbasetech.onrender.com/

# Каталог компаний
curl https://stanbasetech.onrender.com/companies

# API статус
curl https://stanbasetech.onrender.com/test-db
```

## Обновления

### Автоматический деплой
- При push в main ветку
- Автоматическая сборка
- Автоматический деплой

### Ручной деплой
1. Push изменений в GitHub
2. Ожидание завершения сборки
3. Проверка работоспособности

### Откат изменений
1. Откат к предыдущему коммиту
2. Push изменений
3. Ожидание пересборки

## Безопасность

### Переменные окружения
- **SECRET_KEY** - для сессий
- **DATABASE_URL** - для подключения к БД
- **Не хранить в коде** - только в Render Dashboard

### HTTPS
- Автоматическое SSL сертификаты
- Принудительное перенаправление на HTTPS

### База данных
- Изолированная PostgreSQL
- Автоматические бэкапы
- Ограниченный доступ

## Производительность

### Оптимизации
- **Статические файлы** - кэширование
- **База данных** - индексы и оптимизация запросов
- **Шаблоны** - минификация HTML

### Мониторинг
- **Response time** - время отклика
- **Database queries** - количество запросов
- **Memory usage** - использование памяти

## Резервное копирование

### База данных
- **Автоматические бэкапы** - Render PostgreSQL
- **Ручные экспорты** - через API эндпоинты
- **Восстановление** - из бэкапов Render

### Код
- **GitHub** - версионирование
- **Render** - автоматические деплои
- **Локальные копии** - для разработки

## Troubleshooting

### Частые проблемы

#### Ошибка подключения к БД
```bash
# Проверка DATABASE_URL
echo $DATABASE_URL

# Проверка доступности БД
curl https://stanbasetech.onrender.com/test-db
```

#### Ошибки миграции
```bash
# Проверка логов
# Render Dashboard → Logs

# Повторный запуск миграции
curl https://stanbasetech.onrender.com/run-migration
```

#### Проблемы с зависимостями
```bash
# Проверка requirements.txt
# Обновление зависимостей
# Пересборка приложения
```

### Логи и отладка

#### Просмотр логов
```bash
# Render Dashboard → Logs
# Фильтрация по времени
# Поиск ошибок
```

#### Отладка в продакшене
```python
# Добавление логирования
import logging
logging.basicConfig(level=logging.INFO)

# Проверка состояния
@app.get("/debug")
def debug_info():
    return {"status": "ok", "timestamp": datetime.now()}
```

## Масштабирование

### Горизонтальное масштабирование
- **Load Balancer** - готовность к балансировщику
- **Multiple instances** - несколько экземпляров
- **Database pooling** - пулы соединений

### Вертикальное масштабирование
- **Memory upgrade** - увеличение RAM
- **CPU upgrade** - увеличение CPU
- **Database upgrade** - увеличение ресурсов БД

## CI/CD

### GitHub Actions (опционально)
```yaml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        run: |
          # Автоматический деплой
```

### Тестирование перед деплоем
```bash
# Локальные тесты
python -m pytest

# Проверка синтаксиса
python -m py_compile main.py

# Проверка зависимостей
pip check
``` 