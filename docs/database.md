# База данных

## Обзор

Stanbase использует реляционную базу данных с SQLAlchemy ORM. В разработке используется SQLite, в продакшене - PostgreSQL.

## Схема базы данных

### 🏢 Основные сущности

#### Company (Компании)
```sql
CREATE TABLE company (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    country_id INTEGER,
    city_id INTEGER,
    stage_id INTEGER,
    industry VARCHAR(100),
    founded_date DATE,
    website VARCHAR(255),
    logo VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Связи:**
- `country_id` → `country.id`
- `city_id` → `city.id`
- `stage_id` → `company_stage.id`

#### Investor (Инвесторы)
```sql
CREATE TABLE investor (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- 'angel', 'venture', 'other'
    description TEXT,
    country_id INTEGER,
    city_id INTEGER,
    focus TEXT,
    stages TEXT,
    website VARCHAR(255),
    logo VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Deal (Сделки)
```sql
CREATE TABLE deal (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL,
    type VARCHAR(50), -- 'seed', 'series_a', 'series_b', etc.
    amount DECIMAL(15,2),
    valuation DECIMAL(15,2),
    currency_id INTEGER,
    date DATE,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Job (Вакансии)
```sql
CREATE TABLE job (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company_id INTEGER,
    description TEXT,
    requirements TEXT,
    city VARCHAR(100),
    job_type VARCHAR(50), -- 'fulltime', 'parttime', 'remote'
    salary_min INTEGER,
    salary_max INTEGER,
    contact VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### News (Новости)
```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    content TEXT,
    date DATE,
    source VARCHAR(255),
    url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Event (События)
```sql
CREATE TABLE event (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    date DATE,
    location VARCHAR(255),
    url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Person (Люди)
```sql
CREATE TABLE person (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    position VARCHAR(255),
    linkedin VARCHAR(255),
    email VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 📚 Справочники

#### Country (Страны)
```sql
CREATE TABLE country (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(3),
    status VARCHAR(20) DEFAULT 'active'
);
```

#### City (Города)
```sql
CREATE TABLE city (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_id INTEGER,
    status VARCHAR(20) DEFAULT 'active'
);
```

#### Category (Категории)
```sql
CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active'
);
```

#### Currency (Валюты)
```sql
CREATE TABLE currency (
    id INTEGER PRIMARY KEY,
    code VARCHAR(3) NOT NULL,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(5),
    status VARCHAR(20) DEFAULT 'active'
);
```

#### CompanyStage (Стадии компаний)
```sql
CREATE TABLE company_stage (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active'
);
```

### 🔗 Связующие таблицы

#### company_person (Команды компаний)
```sql
CREATE TABLE company_person (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    position VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### investor_company (Портфели инвесторов)
```sql
CREATE TABLE investor_company (
    id INTEGER PRIMARY KEY,
    investor_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### portfolio_entry (Записи портфелей)
```sql
CREATE TABLE portfolio_entry (
    id INTEGER PRIMARY KEY,
    investor_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    deal_id INTEGER,
    investment_amount DECIMAL(15,2),
    investment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Индексы

### Основные индексы для поиска
```sql
-- Компании
CREATE INDEX idx_company_name ON company(name);
CREATE INDEX idx_company_country ON company(country_id);
CREATE INDEX idx_company_stage ON company(stage_id);
CREATE INDEX idx_company_status ON company(status);

-- Инвесторы
CREATE INDEX idx_investor_name ON investor(name);
CREATE INDEX idx_investor_type ON investor(type);
CREATE INDEX idx_investor_country ON investor(country_id);

-- Вакансии
CREATE INDEX idx_job_title ON job(title);
CREATE INDEX idx_job_company ON job(company_id);
CREATE INDEX idx_job_city ON job(city);

-- Сделки
CREATE INDEX idx_deal_company ON deal(company_id);
CREATE INDEX idx_deal_date ON deal(date);
```

## Миграции

### Локальная разработка (SQLite)

```python
# Добавление колонки logo к таблице investor
ALTER TABLE investor ADD COLUMN logo VARCHAR(255);

# Создание таблицы currency
CREATE TABLE currency (
    id INTEGER PRIMARY KEY,
    code VARCHAR(3) NOT NULL,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(5),
    status VARCHAR(20) DEFAULT 'active'
);

# Добавление колонки currency_id к таблице deal
ALTER TABLE deal ADD COLUMN currency_id INTEGER;
```

### Продакшен (PostgreSQL)

```python
# migrate_to_prod.py
def migrate_production_database():
    # Проверка и создание таблицы currency
    # Проверка и добавление колонки logo к investor
    # Проверка и добавление колонки currency_id к deal
    # Обновление существующих записей
```

## Тестовые данные

### Инициализация (init_db.py)

```python
def create_full_test_data():
    # Создание справочников
    # Создание компаний (15 штук)
    # Создание инвесторов (15 штук)
    # Создание сделок (15 штук)
    # Создание вакансий (15 штук)
    # Создание новостей (15 штук)
    # Создание событий (15 штук)
    # Создание людей и связей
```

### Типы тестовых данных

- **Компании:** SaaS, AI, Fintech, E-commerce
- **Инвесторы:** Венчурные фонды, бизнес-ангелы
- **Сделки:** Seed, Series A, Series B
- **Вакансии:** Разработчики, менеджеры, дизайнеры
- **География:** Казахстан, Узбекистан, Кыргызстан

## Оптимизация запросов

### Eager Loading
```python
# Загрузка связанных данных
companies = db.query(Company).options(
    joinedload(Company.deals).joinedload(Deal.currency),
    joinedload(Company.people),
    joinedload(Company.country),
    joinedload(Company.city)
).all()
```

### Фильтрация
```python
# Построение динамических запросов
query = db.query(Company)
if search:
    query = query.filter(Company.name.ilike(f"%{search}%"))
if country:
    query = query.join(Country).filter(Country.name == country)
```

### Пагинация
```python
# Ограничение результатов
companies = query.offset((page - 1) * per_page).limit(per_page).all()
```

## Резервное копирование

### Экспорт данных
```python
def export_data():
    # Экспорт всех таблиц в JSON
    # Сохранение в файл
    # Отправка на сервер
```

### Импорт данных
```python
def import_data(data):
    # Проверка структуры данных
    # Upsert записей
    # Обновление связей
```

## Мониторинг

### Состояние БД
```python
@app.get("/test-db")
def test_db():
    # Подсчет записей в таблицах
    # Проверка структуры таблиц
    # Возврат статистики
``` 