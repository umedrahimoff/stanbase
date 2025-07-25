# Разработка

## Настройка среды разработки

### Требования

- **Python 3.9+**
- **Git**
- **SQLite** (для локальной разработки)
- **Редактор кода** (VS Code, PyCharm, etc.)

### Установка зависимостей

```bash
# Клонирование репозитория
git clone https://github.com/your-username/stanbase.git
cd stanbase

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка базы данных

```bash
# Инициализация SQLite базы данных
python init_db.py

# Проверка создания таблиц
sqlite3 instance/stanbase.db ".tables"
```

### Запуск приложения

```bash
# Запуск в режиме разработки
python main.py

# Или через uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Структура проекта

### Основные файлы

```
stanbase/
├── main.py              # Основное приложение
├── models.py            # Модели SQLAlchemy
├── db.py               # Настройки БД
├── init_db.py          # Инициализация БД
├── migrate_to_prod.py  # Миграции для продакшена
├── requirements.txt    # Зависимости
├── Procfile           # Конфигурация Render
├── templates/         # Jinja2 шаблоны
├── static/           # Статические файлы
└── docs/            # Документация
```

### Шаблоны

```
templates/
├── layout.html              # Базовый шаблон
├── index.html               # Главная страница
├── 404.html                 # Страница ошибки
├── admin/                   # Админ-панель
│   ├── layout.html
│   ├── dashboard.html
│   ├── companies/
│   ├── investors/
│   ├── jobs/
│   ├── deals/
│   ├── currencies/
│   └── users/
├── public/                  # Публичные страницы
│   ├── companies/
│   ├── investors/
│   ├── jobs/
│   ├── news/
│   ├── events/
│   └── podcasts/
├── auth/                    # Аутентификация
└── dashboard/               # Личные кабинеты
```

## Работа с кодом

### Стиль кода

#### Python (PEP 8)
```python
# Импорты
import os
from typing import List, Optional
from fastapi import FastAPI, Request
from sqlalchemy.orm import Session

# Функции и классы
def get_companies(db: Session, limit: int = 20) -> List[Company]:
    """Получить список компаний."""
    return db.query(Company).limit(limit).all()

class CompanyService:
    """Сервис для работы с компаниями."""
    
    def __init__(self, db: Session):
        self.db = db
```

#### HTML/Jinja2
```html
<!-- Комментарии -->
{% comment %} Блок комментария {% endcomment %}

<!-- Условия -->
{% if company.logo %}
    <img src="{{ company.logo }}" alt="logo">
{% else %}
    <img src="https://api.dicebear.com/7.x/identicon/svg?seed={{ company.name|urlencode }}" alt="logo">
{% endif %}

<!-- Циклы -->
{% for company in companies %}
    <div class="company-card">
        <h3>{{ company.name }}</h3>
        <p>{{ company.description }}</p>
    </div>
{% endfor %}
```

### Работа с базой данных

#### Создание запросов
```python
# Простой запрос
companies = db.query(Company).all()

# Фильтрация
active_companies = db.query(Company).filter(Company.status == 'active').all()

# Поиск
search_results = db.query(Company).filter(
    Company.name.ilike(f"%{search_term}%")
).all()

# Связи
companies_with_deals = db.query(Company).options(
    joinedload(Company.deals)
).all()
```

#### Создание записей
```python
# Создание новой компании
new_company = Company(
    name="Test Company",
    description="Test description",
    country_id=1,
    city_id=1,
    status="active"
)
db.add(new_company)
db.commit()
```

#### Обновление записей
```python
# Обновление компании
company = db.query(Company).filter(Company.id == company_id).first()
if company:
    company.name = "Updated Name"
    company.description = "Updated description"
    db.commit()
```

### Работа с формами

#### Обработка POST запросов
```python
@app.post("/admin/companies/create")
async def admin_create_company_post(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    country: int = Form(...),
    city: int = Form(...),
    logo: UploadFile = File(None)
):
    # Валидация данных
    if not name or not description:
        return RedirectResponse("/admin/companies/create?error=validation", status_code=302)
    
    # Сохранение файла
    if logo:
        logo_path = save_uploaded_file(logo)
    else:
        logo_path = None
    
    # Создание записи
    db = SessionLocal()
    try:
        company = Company(
            name=name,
            description=description,
            country_id=country,
            city_id=city,
            logo=logo_path
        )
        db.add(company)
        db.commit()
        return RedirectResponse("/admin/companies", status_code=302)
    finally:
        db.close()
```

### Работа с шаблонами

#### Передача данных
```python
@app.get("/companies")
async def companies(
    request: Request,
    q: Optional[str] = None,
    country: Optional[str] = None,
    stage: Optional[str] = None
):
    db = SessionLocal()
    try:
        # Построение запроса
        query = db.query(Company)
        if q:
            query = query.filter(Company.name.ilike(f"%{q}%"))
        if country:
            query = query.join(Country).filter(Country.name == country)
        
        companies = query.all()
        
        # Получение справочников
        countries = db.query(Country).all()
        stages = db.query(CompanyStage).all()
        
        return templates.TemplateResponse("public/companies/list.html", {
            "request": request,
            "companies": companies,
            "countries": [c.name for c in countries],
            "stages": [s.name for s in stages]
        })
    finally:
        db.close()
```

#### Условная логика в шаблонах
```html
<!-- Проверка существования данных -->
{% if companies %}
    <div class="companies-list">
        {% for company in companies %}
            <div class="company-card">
                <h3>{{ company.name }}</h3>
                {% if company.description %}
                    <p>{{ company.description }}</p>
                {% endif %}
            </div>
        {% endfor %}
    </div>
{% else %}
    <p>Компании не найдены</p>
{% endif %}
```

## Отладка

### Логирование
```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Использование в коде
logger.info("Загрузка компаний")
logger.error("Ошибка при загрузке данных: %s", str(e))
```

### Отладка в браузере
```python
# Добавление отладочной информации
@app.get("/debug")
async def debug_info():
    return {
        "timestamp": datetime.now(),
        "database_url": "configured" if DATABASE_URL else "not configured",
        "companies_count": db.query(Company).count()
    }
```

### Проверка синтаксиса
```bash
# Проверка Python файлов
python3 -m py_compile main.py
python3 -m py_compile models.py

# Проверка всех Python файлов
find . -name "*.py" -exec python3 -m py_compile {} \;
```

## Тестирование

### Ручное тестирование
```bash
# Запуск приложения
python main.py

# Тестирование эндпоинтов
curl http://localhost:8000/
curl http://localhost:8000/companies
curl http://localhost:8000/admin
```

### Тестирование базы данных
```bash
# Подключение к SQLite
sqlite3 instance/stanbase.db

# Проверка таблиц
.tables

# Проверка данных
SELECT COUNT(*) FROM company;
SELECT COUNT(*) FROM investor;
```

## Git workflow

### Создание веток
```bash
# Создание feature ветки
git checkout -b feature/new-feature

# Создание bugfix ветки
git checkout -b bugfix/fix-issue
```

### Коммиты
```bash
# Добавление изменений
git add .

# Создание коммита
git commit -m "Добавлена функция поиска компаний"

# Push изменений
git push origin feature/new-feature
```

### Merge в main
```bash
# Переключение на main
git checkout main

# Pull последних изменений
git pull origin main

# Merge feature ветки
git merge feature/new-feature

# Push в main
git push origin main
```

## Производительность

### Оптимизация запросов
```python
# Использование joinedload для избежания N+1 проблем
companies = db.query(Company).options(
    joinedload(Company.country),
    joinedload(Company.city),
    joinedload(Company.deals)
).all()

# Пагинация для больших списков
companies = db.query(Company).offset(offset).limit(limit).all()
```

### Кэширование
```python
# Кэширование справочников
from functools import lru_cache

@lru_cache(maxsize=128)
def get_countries():
    db = SessionLocal()
    try:
        return db.query(Country).all()
    finally:
        db.close()
```

## Безопасность

### Валидация входных данных
```python
# Проверка типов данных
if not isinstance(company_id, int):
    raise ValueError("Invalid company ID")

# Санитизация строк
import html
safe_name = html.escape(company_name)
```

### Защита от SQL Injection
```python
# Использование ORM вместо raw SQL
# Правильно:
companies = db.query(Company).filter(Company.name.ilike(f"%{search}%")).all()

# Неправильно:
# companies = db.execute(f"SELECT * FROM company WHERE name LIKE '%{search}%'")
```

### Аутентификация
```python
# Проверка сессии
def require_auth(request: Request):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return request.session["user_id"]
```

## Полезные команды

### Разработка
```bash
# Запуск с автоперезагрузкой
uvicorn main:app --reload

# Проверка зависимостей
pip check

# Обновление зависимостей
pip install --upgrade -r requirements.txt
```

### База данных
```bash
# Резервная копия SQLite
cp instance/stanbase.db instance/stanbase_backup.db

# Восстановление из бэкапа
cp instance/stanbase_backup.db instance/stanbase.db

# Очистка базы данных
rm instance/stanbase.db
python init_db.py
```

### Git
```bash
# Просмотр изменений
git status
git diff

# Отмена изменений
git checkout -- filename
git reset --hard HEAD

# Просмотр истории
git log --oneline
git log --graph --oneline --all
``` 