# API

## Обзор

REST API для работы с данными компаний, инвесторов и связанных сущностей. Построен на FastAPI.

**Базовый URL:** `https://stanbasetech.onrender.com`

## Аутентификация

Сессионная аутентификация через cookies. Время жизни сессии: 24 часа.

## Публичные API

### Главная страница
- **GET /** - Главная страница с обзором данных

### Компании
- **GET /companies** - Каталог компаний
  - Параметры: `q`, `country`, `stage`, `industry`, `page`, `per_page`
- **GET /company/{id}** - Детальная страница компании

### Инвесторы
- **GET /investors** - Каталог инвесторов
  - Параметры: `q`, `country`, `focus`, `stages`, `type`, `page`, `per_page`
- **GET /investor/{id}** - Детальная страница инвестора

### Вакансии
- **GET /jobs** - Список вакансий
  - Параметры: `q`, `city`, `job_type`, `company`, `salary_min`, `salary_max`, `page`, `per_page`
- **GET /job/{id}** - Детальная страница вакансии

### Контент
- **GET /news** - Список новостей
  - Параметры: `page`, `per_page`
- **GET /news/{id}** - Детальная страница новости
- **GET /events** - Список событий
  - Параметры: `page`, `per_page`
- **GET /event/{id}** - Детальная страница события
- **GET /podcasts** - Список подкастов
  - Параметры: `page`, `per_page`

## Админ API

### Аутентификация
- **POST /login** - Вход в систему
  - Параметры: `email`, `password`
- **GET /logout** - Выход из системы

### Дашборд
- **GET /admin** - Главная страница админки

### Управление компаниями
- **GET /admin/companies** - Список компаний
  - Параметры: `q`, `status`, `page`, `per_page`
- **GET /admin/companies/create** - Форма создания
- **POST /admin/companies/create** - Создание компании
  - Параметры: `name`, `description`, `country`, `city`, `stage`, `industry`, `founded_date`, `website`, `logo`, `status`
- **GET /admin/companies/edit/{id}** - Форма редактирования
- **POST /admin/companies/edit/{id}** - Обновление компании
- **POST /admin/companies/delete/{id}** - Удаление компании

### Управление инвесторами
- **GET /admin/investors** - Список инвесторов
  - Параметры: `q`, `type`, `status`, `page`, `per_page`
- **GET /admin/investors/create** - Форма создания
- **POST /admin/investors/create** - Создание инвестора
  - Параметры: `name`, `type`, `description`, `country`, `city`, `focus`, `stages`, `website`, `logo`, `status`
- **GET /admin/investors/edit/{id}** - Форма редактирования
- **POST /admin/investors/edit/{id}** - Обновление инвестора
- **POST /admin/investors/delete/{id}** - Удаление инвестора

### Управление вакансиями
- **GET /admin/jobs** - Список вакансий
  - Параметры: `q`, `company`, `status`, `page`, `per_page`
- **GET /admin/jobs/create** - Форма создания
- **POST /admin/jobs/create** - Создание вакансии
  - Параметры: `title`, `company`, `description`, `requirements`, `city`, `job_type`, `salary_min`, `salary_max`, `contact`, `status`
- **GET /admin/jobs/edit/{id}** - Форма редактирования
- **POST /admin/jobs/edit/{id}** - Обновление вакансии
- **POST /admin/jobs/delete/{id}** - Удаление вакансии

### Управление контентом
- **GET /admin/news** - Список новостей
- **GET /admin/events** - Список событий
- **GET /admin/podcasts** - Список подкастов

### Управление сделками
- **GET /admin/deals** - Список сделок
  - Параметры: `q`, `company`, `investor`, `status`, `page`, `per_page`
- **GET /admin/deals/create** - Форма создания
- **POST /admin/deals/create** - Создание сделки
  - Параметры: `type`, `amount`, `valuation`, `date`, `currency_id`, `company_id`, `investors`, `status`
- **GET /admin/deals/edit/{id}** - Форма редактирования
- **POST /admin/deals/edit/{id}** - Обновление сделки
- **POST /admin/deals/delete/{id}** - Удаление сделки

### Справочники
- **GET /admin/countries** - Список стран
- **GET /admin/cities** - Список городов
- **GET /admin/categories** - Список категорий
- **GET /admin/stages** - Список стадий
- **GET /admin/currencies** - Список валют
- **GET /admin/currencies/create** - Форма создания валюты
- **POST /admin/currencies/create** - Создание валюты
  - Параметры: `code`, `name`, `symbol`, `status`
- **GET /admin/currencies/edit/{id}** - Форма редактирования валюты
- **POST /admin/currencies/edit/{id}** - Обновление валюты
- **POST /admin/currencies/delete/{id}** - Удаление валюты

### Пользователи
- **GET /admin/users** - Список пользователей
- **GET /admin/admins** - Список администраторов

## Системные API

### Миграции и данные
- **GET /run-migration** - Выполнение миграций БД
- **POST /import-data** - Импорт данных
  - Параметры: `data` (JSON объект)
- **GET /test-db** - Тестирование состояния БД

## Параметры запросов

### Общие параметры
- `page` (integer) - номер страницы (по умолчанию 1)
- `per_page` (integer) - элементов на странице (по умолчанию 20, максимум 100)
- `q` (string) - поисковый запрос
- `status` (string) - фильтр по статусу (active, inactive)

### Фильтры компаний
- `country` (string) - фильтр по стране
- `stage` (string) - фильтр по стадии развития
- `industry` (string) - фильтр по отрасли

### Фильтры инвесторов
- `type` (string) - тип инвестора (angel, venture, other)
- `focus` (string) - фокус инвестирования
- `stages` (string) - стадии инвестирования

### Фильтры вакансий
- `city` (string) - фильтр по городу
- `job_type` (string) - тип работы (fulltime, parttime, remote)
- `company` (integer) - ID компании
- `salary_min` (integer) - минимальная зарплата
- `salary_max` (integer) - максимальная зарплата

### Фильтры сделок
- `company` (integer) - ID компании
- `investor` (integer) - ID инвестора

## Структуры данных

### Компания
```json
{
  "id": 1,
  "name": "TechCorp",
  "description": "Инновационная технологическая компания",
  "country": "Казахстан",
  "city": "Алматы",
  "stage": "Series A",
  "industry": "SaaS",
  "founded_date": "2020-01-15",
  "website": "https://techcorp.kz",
  "logo": "/static/logos/techcorp.png",
  "status": "active"
}
```

### Инвестор
```json
{
  "id": 1,
  "name": "Central Asia Ventures",
  "type": "venture",
  "description": "Венчурный фонд Центральной Азии",
  "country": "Казахстан",
  "city": "Алматы",
  "focus": "AI, SaaS, Fintech",
  "stages": "Seed, Series A, Series B",
  "website": "https://caventures.kz",
  "logo": "/static/logos/cav.png",
  "status": "active"
}
```

### Вакансия
```json
{
  "id": 1,
  "title": "Senior Python Developer",
  "company_id": 1,
  "company_name": "TechCorp",
  "description": "Мы ищем опытного Python разработчика...",
  "requirements": "Опыт работы с FastAPI, SQLAlchemy...",
  "city": "Алматы",
  "job_type": "fulltime",
  "salary_min": 2000,
  "salary_max": 4000,
  "contact": "hr@techcorp.kz",
  "status": "active"
}
```

### Сделка
```json
{
  "id": 1,
  "type": "Series A",
  "amount": 1000000,
  "valuation": 5000000,
  "date": "2023-06-15",
  "currency": {
    "id": 1,
    "code": "USD",
    "symbol": "$"
  },
  "company_id": 1,
  "company_name": "TechCorp",
  "investors": [
    {
      "id": 1,
      "name": "Central Asia Ventures"
    }
  ],
  "status": "active"
}
```

## Статус коды

- `200` - Успешный ответ
- `302` - Redirect (для форм и аутентификации)
- `400` - Неверный запрос (ошибка валидации)
- `401` - Не авторизован
- `404` - Страница не найдена
- `500` - Внутренняя ошибка сервера

## Ограничения

### Rate Limiting
- Публичные эндпоинты: 100 запросов в минуту
- Админ эндпоинты: 50 запросов в минуту

### Размеры файлов
- Логотипы: максимум 5MB
- Изображения: максимум 10MB
- JSON импорт: максимум 50MB

## Примеры запросов

### Поиск компаний
```bash
curl "https://stanbasetech.onrender.com/companies?country=Казахстан&industry=SaaS&q=AI"
```

### Создание компании
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/companies/create" \
  -H "Content-Type: multipart/form-data" \
  -F "name=AI Startup" \
  -F "description=Инновационная AI компания" \
  -F "country=1" \
  -F "city=1" \
  -F "industry=AI" \
  -F "status=active"
```

### Проверка БД
```bash
curl "https://stanbasetech.onrender.com/test-db"
```

## Обработка ошибок

### JSON ошибки
```json
{
  "error": "Validation error",
  "details": "Field 'name' is required",
  "field": "name"
}
```

### HTML ошибки
```html
<div class="alert alert-danger">
  <h4>Ошибка</h4>
  <p>Описание ошибки</p>
</div>
``` 