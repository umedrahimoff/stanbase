# API

## Обзор

Stanbase предоставляет REST API для работы с данными компаний, инвесторов и связанных сущностей. API построен на FastAPI и поддерживает как HTML-ответы для веб-интерфейса, так и JSON для программного доступа.

## Базовый URL

```
https://stanbasetech.onrender.com
```

## Аутентификация

API использует сессионную аутентификацию. Для доступа к защищенным эндпоинтам требуется авторизация через веб-интерфейс.

### Сессии
- Сессии хранятся в cookies
- Время жизни сессии: 24 часа
- Автоматическое продление при активности

## Основные эндпоинты

### 🏠 Главная страница

**GET /** - Главная страница с обзором данных

**Описание:** Возвращает главную страницу с карточками компаний, инвесторов, новостей и других сущностей.

**Параметры:** Отсутствуют

**Ответ:** HTML страница

**Пример запроса:**
```bash
curl https://stanbasetech.onrender.com/
```

**Статус коды:**
- `200` - Успешный ответ
- `500` - Внутренняя ошибка сервера

### 🏢 Компании

#### GET /companies - Каталог компаний

**Описание:** Возвращает список компаний с возможностью фильтрации и поиска.

**Параметры запроса:**
- `q` (string, optional) - поисковый запрос по названию
- `country` (string, optional) - фильтр по стране
- `stage` (string, optional) - фильтр по стадии развития
- `industry` (string, optional) - фильтр по отрасли
- `page` (integer, optional) - номер страницы (по умолчанию 1)
- `per_page` (integer, optional) - элементов на странице (по умолчанию 20)

**Пример запроса:**
```bash
# Поиск компаний в Казахстане
curl "https://stanbasetech.onrender.com/companies?country=Казахстан&q=tech"

# Фильтр по стадии и отрасли
curl "https://stanbasetech.onrender.com/companies?stage=Seed&industry=SaaS"

# Пагинация
curl "https://stanbasetech.onrender.com/companies?page=2&per_page=10"
```

**Ответ:** HTML страница со списком компаний

**Статус коды:**
- `200` - Успешный ответ
- `400` - Неверные параметры запроса
- `500` - Внутренняя ошибка сервера

---

#### GET /company/{id} - Детальная страница компании

**Описание:** Возвращает детальную информацию о конкретной компании.

**Параметры пути:**
- `id` (integer, required) - ID компании

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/company/1"
```

**Ответ:** HTML страница с полной информацией о компании

**Структура данных компании:**
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
  "deals": [
    {
      "id": 1,
      "type": "Series A",
      "amount": 1000000,
      "currency": "USD",
      "date": "2023-06-15"
    }
  ],
  "people": [
    {
      "id": 1,
      "name": "Иван Иванов",
      "position": "CEO",
      "linkedin": "https://linkedin.com/in/ivan"
    }
  ],
  "jobs": [
    {
      "id": 1,
      "title": "Senior Developer",
      "city": "Алматы",
      "job_type": "fulltime"
    }
  ]
}
```

**Статус коды:**
- `200` - Успешный ответ
- `404` - Компания не найдена
- `500` - Внутренняя ошибка сервера

### 💰 Инвесторы

#### GET /investors - Каталог инвесторов

**Описание:** Возвращает список инвесторов с возможностью фильтрации.

**Параметры запроса:**
- `q` (string, optional) - поисковый запрос по названию
- `country` (string, optional) - фильтр по стране
- `focus` (string, optional) - фильтр по фокусу инвестирования
- `stages` (string, optional) - фильтр по стадиям инвестирования
- `type` (string, optional) - тип инвестора (angel, venture, other)
- `page` (integer, optional) - номер страницы
- `per_page` (integer, optional) - элементов на странице

**Пример запроса:**
```bash
# Поиск венчурных фондов в Узбекистане
curl "https://stanbasetech.onrender.com/investors?country=Узбекистан&type=venture"

# Фильтр по фокусу
curl "https://stanbasetech.onrender.com/investors?focus=AI&stages=Seed"
```

**Ответ:** HTML страница со списком инвесторов

---

#### GET /investor/{id} - Детальная страница инвестора

**Описание:** Возвращает детальную информацию о конкретном инвесторе.

**Параметры пути:**
- `id` (integer, required) - ID инвестора

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/investor/1"
```

**Ответ:** HTML страница с полной информацией об инвесторе

**Структура данных инвестора:**
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
  "portfolio": [
    {
      "company_id": 1,
      "company_name": "TechCorp",
      "investment_amount": 500000,
      "investment_date": "2023-01-15"
    }
  ],
  "team": [
    {
      "id": 1,
      "name": "Анна Петрова",
      "position": "Managing Partner",
      "linkedin": "https://linkedin.com/in/anna"
    }
  ]
}
```

### 💼 Вакансии

#### GET /jobs - Список вакансий

**Описание:** Возвращает список вакансий с возможностью фильтрации.

**Параметры запроса:**
- `q` (string, optional) - поисковый запрос по названию
- `city` (string, optional) - фильтр по городу
- `job_type` (string, optional) - тип работы (fulltime, parttime, remote)
- `company` (integer, optional) - ID компании
- `salary_min` (integer, optional) - минимальная зарплата
- `salary_max` (integer, optional) - максимальная зарплата
- `page` (integer, optional) - номер страницы
- `per_page` (integer, optional) - элементов на странице

**Пример запроса:**
```bash
# Поиск удаленных вакансий разработчика
curl "https://stanbasetech.onrender.com/jobs?q=developer&job_type=remote"

# Вакансии в конкретной компании
curl "https://stanbasetech.onrender.com/jobs?company=1"

# Фильтр по зарплате
curl "https://stanbasetech.onrender.com/jobs?salary_min=1000&salary_max=5000"
```

**Ответ:** HTML страница со списком вакансий

---

#### GET /job/{id} - Детальная страница вакансии

**Описание:** Возвращает детальную информацию о конкретной вакансии.

**Параметры пути:**
- `id` (integer, required) - ID вакансии

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/job/1"
```

**Ответ:** HTML страница с полной информацией о вакансии

**Структура данных вакансии:**
```json
{
  "id": 1,
  "title": "Senior Python Developer",
  "company": {
    "id": 1,
    "name": "TechCorp",
    "logo": "/static/logos/techcorp.png"
  },
  "description": "Мы ищем опытного Python разработчика...",
  "requirements": "Опыт работы с FastAPI, SQLAlchemy...",
  "city": "Алматы",
  "job_type": "fulltime",
  "salary_min": 2000,
  "salary_max": 4000,
  "contact": "hr@techcorp.kz",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 📰 Новости и события

#### GET /news - Список новостей

**Описание:** Возвращает список новостей с пагинацией.

**Параметры запроса:**
- `page` (integer, optional) - номер страницы
- `per_page` (integer, optional) - элементов на странице

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/news?page=1&per_page=10"
```

**Ответ:** HTML страница со списком новостей

---

#### GET /news/{id} - Детальная страница новости

**Описание:** Возвращает полный текст новости.

**Параметры пути:**
- `id` (integer, required) - ID новости

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/news/1"
```

**Ответ:** HTML страница с полной новостью

---

#### GET /events - Список событий

**Описание:** Возвращает список событий и мероприятий.

**Параметры запроса:**
- `page` (integer, optional) - номер страницы
- `per_page` (integer, optional) - элементов на странице

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/events"
```

**Ответ:** HTML страница со списком событий

---

#### GET /event/{id} - Детальная страница события

**Описание:** Возвращает детальную информацию о событии.

**Параметры пути:**
- `id` (integer, required) - ID события

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/event/1"
```

**Ответ:** HTML страница с полной информацией о событии

## Админ API

### 🔐 Аутентификация

#### POST /login - Вход в систему

**Описание:** Аутентификация пользователя и создание сессии.

**Параметры формы:**
- `email` (string, required) - email пользователя
- `password` (string, required) - пароль

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@example.com&password=password123"
```

**Ответ:** Redirect на админ-панель или страницу ошибки

**Статус коды:**
- `302` - Успешная аутентификация (redirect)
- `401` - Неверные учетные данные
- `400` - Неверные параметры

---

#### GET /logout - Выход из системы

**Описание:** Завершение сессии пользователя.

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/logout"
```

**Ответ:** Redirect на главную страницу

### 📊 Админ-панель

#### GET /admin - Главная страница админки

**Описание:** Возвращает дашборд с статистикой.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin"
```

**Ответ:** HTML страница с дашбордом

### 🏢 Управление компаниями

#### GET /admin/companies - Список компаний

**Описание:** Возвращает список компаний для администрирования.

**Параметры запроса:**
- `q` (string, optional) - поиск по названию
- `status` (string, optional) - фильтр по статусу (active, inactive)
- `page` (integer, optional) - номер страницы
- `per_page` (integer, optional) - элементов на странице

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/companies?status=active&page=1"
```

**Ответ:** HTML страница со списком компаний

---

#### GET /admin/companies/create - Форма создания компании

**Описание:** Возвращает форму для создания новой компании.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/companies/create"
```

**Ответ:** HTML форма

---

#### POST /admin/companies/create - Создание компании

**Описание:** Создает новую компанию.

**Параметры формы:**
- `name` (string, required) - название компании
- `description` (string, required) - описание
- `country` (integer, required) - ID страны
- `city` (integer, required) - ID города
- `stage` (integer, optional) - ID стадии
- `industry` (string, optional) - отрасль
- `founded_date` (date, optional) - дата основания
- `website` (string, optional) - веб-сайт
- `logo` (file, optional) - логотип
- `status` (string, optional) - статус (active, inactive)

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/companies/create" \
  -H "Content-Type: multipart/form-data" \
  -F "name=New Tech Company" \
  -F "description=Инновационная компания" \
  -F "country=1" \
  -F "city=1" \
  -F "industry=SaaS" \
  -F "status=active" \
  -F "logo=@/path/to/logo.png"
```

**Ответ:** Redirect на список компаний или страницу ошибки

**Статус коды:**
- `302` - Успешное создание (redirect)
- `400` - Ошибка валидации
- `401` - Не авторизован
- `500` - Внутренняя ошибка

---

#### GET /admin/companies/edit/{id} - Форма редактирования

**Описание:** Возвращает форму для редактирования компании.

**Параметры пути:**
- `id` (integer, required) - ID компании

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/companies/edit/1"
```

**Ответ:** HTML форма с данными компании

---

#### POST /admin/companies/edit/{id} - Обновление компании

**Описание:** Обновляет существующую компанию.

**Параметры пути:**
- `id` (integer, required) - ID компании

**Параметры формы:** Аналогично созданию

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/companies/edit/1" \
  -H "Content-Type: multipart/form-data" \
  -F "name=Updated Company Name" \
  -F "description=Обновленное описание" \
  -F "country=1" \
  -F "city=1"
```

**Ответ:** Redirect на страницу компании или список

---

#### POST /admin/companies/delete/{id} - Удаление компании

**Описание:** Удаляет компанию (мягкое удаление).

**Параметры пути:**
- `id` (integer, required) - ID компании

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/companies/delete/1"
```

**Ответ:** Redirect на список компаний

### 💰 Управление инвесторами

#### GET /admin/investors - Список инвесторов

**Описание:** Возвращает список инвесторов для администрирования.

**Параметры запроса:**
- `q` (string, optional) - поиск по названию
- `type` (string, optional) - фильтр по типу
- `status` (string, optional) - фильтр по статусу
- `page` (integer, optional) - номер страницы
- `per_page` (integer, optional) - элементов на странице

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/investors?type=venture&status=active"
```

**Ответ:** HTML страница со списком инвесторов

---

#### GET /admin/investors/create - Форма создания инвестора

**Описание:** Возвращает форму для создания нового инвестора.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/investors/create"
```

**Ответ:** HTML форма

---

#### POST /admin/investors/create - Создание инвестора

**Описание:** Создает нового инвестора.

**Параметры формы:**
- `name` (string, required) - название
- `type` (string, required) - тип (angel, venture, other)
- `description` (string, optional) - описание
- `country` (integer, optional) - ID страны
- `city` (integer, optional) - ID города
- `focus` (string, optional) - фокус инвестирования
- `stages` (string, optional) - стадии инвестирования
- `website` (string, optional) - веб-сайт
- `logo` (file, optional) - логотип
- `status` (string, optional) - статус

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/investors/create" \
  -H "Content-Type: multipart/form-data" \
  -F "name=New Venture Fund" \
  -F "type=venture" \
  -F "description=Венчурный фонд" \
  -F "country=1" \
  -F "focus=AI, SaaS" \
  -F "stages=Seed, Series A"
```

**Ответ:** Redirect на список инвесторов

---

#### GET /admin/investors/edit/{id} - Форма редактирования инвестора

**Описание:** Возвращает форму для редактирования инвестора.

**Параметры пути:**
- `id` (integer, required) - ID инвестора

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/investors/edit/1"
```

**Ответ:** HTML форма с данными инвестора

---

#### POST /admin/investors/edit/{id} - Обновление инвестора

**Описание:** Обновляет существующего инвестора.

**Параметры пути:**
- `id` (integer, required) - ID инвестора

**Параметры формы:** Аналогично созданию

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/investors/edit/1" \
  -H "Content-Type: multipart/form-data" \
  -F "name=Updated Fund Name" \
  -F "type=venture" \
  -F "focus=AI, Fintech, SaaS"
```

**Ответ:** Redirect на страницу инвестора

---

#### POST /admin/investors/delete/{id} - Удаление инвестора

**Описание:** Удаляет инвестора (мягкое удаление).

**Параметры пути:**
- `id` (integer, required) - ID инвестора

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/investors/delete/1"
```

**Ответ:** Redirect на список инвесторов

### 💼 Управление вакансиями

#### GET /admin/jobs - Список вакансий

**Описание:** Возвращает список вакансий для администрирования.

**Параметры запроса:**
- `q` (string, optional) - поиск по названию
- `company` (integer, optional) - фильтр по компании
- `status` (string, optional) - фильтр по статусу
- `page` (integer, optional) - номер страницы
- `per_page` (integer, optional) - элементов на странице

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/jobs?company=1&status=active"
```

**Ответ:** HTML страница со списком вакансий

---

#### GET /admin/jobs/create - Форма создания вакансии

**Описание:** Возвращает форму для создания новой вакансии.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/jobs/create"
```

**Ответ:** HTML форма

---

#### POST /admin/jobs/create - Создание вакансии

**Описание:** Создает новую вакансию.

**Параметры формы:**
- `title` (string, required) - название вакансии
- `company` (integer, required) - ID компании
- `description` (string, required) - описание
- `requirements` (string, optional) - требования
- `city` (string, optional) - город
- `job_type` (string, required) - тип работы (fulltime, parttime, remote)
- `salary_min` (integer, optional) - минимальная зарплата
- `salary_max` (integer, optional) - максимальная зарплата
- `contact` (string, required) - контактная информация
- `status` (string, optional) - статус

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/jobs/create" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "title=Senior Developer&company=1&description=Мы ищем опытного разработчика&job_type=fulltime&city=Алматы&contact=hr@company.com&status=active"
```

**Ответ:** Redirect на список вакансий

---

#### GET /admin/jobs/edit/{id} - Форма редактирования вакансии

**Описание:** Возвращает форму для редактирования вакансии.

**Параметры пути:**
- `id` (integer, required) - ID вакансии

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/jobs/edit/1"
```

**Ответ:** HTML форма с данными вакансии

---

#### POST /admin/jobs/edit/{id} - Обновление вакансии

**Описание:** Обновляет существующую вакансию.

**Параметры пути:**
- `id` (integer, required) - ID вакансии

**Параметры формы:** Аналогично созданию

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/jobs/edit/1" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "title=Updated Job Title&description=Updated description&status=active"
```

**Ответ:** Redirect на страницу вакансии

---

#### POST /admin/jobs/delete/{id} - Удаление вакансии

**Описание:** Удаляет вакансию (мягкое удаление).

**Параметры пути:**
- `id` (integer, required) - ID вакансии

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/admin/jobs/delete/1"
```

**Ответ:** Redirect на список вакансий

### 📰 Управление контентом

#### GET /admin/news - Список новостей

**Описание:** Возвращает список новостей для администрирования.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/news"
```

**Ответ:** HTML страница со списком новостей

---

#### GET /admin/events - Список событий

**Описание:** Возвращает список событий для администрирования.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/events"
```

**Ответ:** HTML страница со списком событий

---

#### GET /admin/podcasts - Список подкастов

**Описание:** Возвращает список подкастов для администрирования.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/admin/podcasts"
```

**Ответ:** HTML страница со списком подкастов

### 🔧 Системные эндпоинты

#### GET /run-migration - Выполнение миграций БД

**Описание:** Выполняет миграции базы данных на продакшене.

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/run-migration"
```

**Ответ:** JSON с результатом миграции

**Пример ответа:**
```json
{
  "success": true,
  "message": "Миграция выполнена успешно",
  "details": {
    "tables_created": 1,
    "columns_added": 2,
    "data_updated": 15
  }
}
```

**Статус коды:**
- `200` - Успешное выполнение
- `500` - Ошибка миграции

---

#### POST /import-data - Импорт данных

**Описание:** Импортирует данные из JSON в базу данных.

**Параметры:**
- `data` (object, required) - данные для импорта

**Требования:** Аутентификация

**Пример запроса:**
```bash
curl -X POST "https://stanbasetech.onrender.com/import-data" \
  -H "Content-Type: application/json" \
  -d '{
    "companies": [
      {
        "name": "New Company",
        "description": "Description",
        "country_id": 1,
        "city_id": 1
      }
    ],
    "investors": [
      {
        "name": "New Investor",
        "type": "venture",
        "country_id": 1
      }
    ]
  }'
```

**Ответ:** JSON с результатом импорта

**Пример ответа:**
```json
{
  "success": true,
  "message": "Данные импортированы успешно",
  "details": {
    "companies_imported": 15,
    "investors_imported": 10,
    "jobs_imported": 20
  }
}
```

**Статус коды:**
- `200` - Успешный импорт
- `400` - Ошибка валидации данных
- `500` - Ошибка импорта

---

#### GET /test-db - Тестирование состояния БД

**Описание:** Проверяет состояние базы данных и возвращает статистику.

**Пример запроса:**
```bash
curl "https://stanbasetech.onrender.com/test-db"
```

**Ответ:** JSON с информацией о БД

**Пример ответа:**
```json
{
  "success": true,
  "counts": {
    "companies": 15,
    "investors": 10,
    "news": 25,
    "events": 8,
    "jobs": 30
  },
  "columns": {
    "company": ["id", "name", "description", "country_id", "city_id", "logo", "status"],
    "investor": ["id", "name", "type", "description", "country_id", "city_id", "logo", "status"]
  },
  "database_url": "configured",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

**Статус коды:**
- `200` - Успешная проверка
- `500` - Ошибка подключения к БД

## Обработка ошибок

### HTTP статусы

- `200` - Успешный запрос
- `302` - Redirect (для форм и аутентификации)
- `400` - Неверный запрос (ошибка валидации)
- `401` - Не авторизован
- `404` - Страница не найдена
- `500` - Внутренняя ошибка сервера

### Обработка исключений

```python
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"error": "Database error", "details": str(exc)}
    )

@app.exception_handler(InternalError)
async def internal_error_handler(request: Request, exc: InternalError):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )
```

### Форматы ошибок

#### JSON ошибки
```json
{
  "error": "Validation error",
  "details": "Field 'name' is required",
  "field": "name",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

#### HTML ошибки
```html
<div class="alert alert-danger">
  <h4>Ошибка</h4>
  <p>Описание ошибки</p>
  <a href="/admin/companies" class="btn btn-primary">Вернуться к списку</a>
</div>
```

## Ограничения и лимиты

### Rate Limiting
- **Публичные эндпоинты:** 100 запросов в минуту
- **Админ эндпоинты:** 50 запросов в минуту
- **API эндпоинты:** 30 запросов в минуту

### Размеры файлов
- **Логотипы:** максимум 5MB
- **Изображения:** максимум 10MB
- **JSON импорт:** максимум 50MB

### Пагинация
- **По умолчанию:** 20 элементов на страницу
- **Максимум:** 100 элементов на страницу
- **Минимум:** 1 элемент на страницу

## Безопасность

### Аутентификация
- Сессионная аутентификация
- Автоматическое завершение сессии через 24 часа
- Защита от CSRF атак

### Валидация данных
- Проверка типов данных
- Санитизация входных данных
- Защита от SQL инъекций через ORM

### Файловые загрузки
- Проверка типов файлов
- Ограничение размера файлов
- Безопасное сохранение в статической папке

## Примеры использования

### Получение списка компаний с фильтрацией
```bash
# Поиск технологических компаний в Казахстане
curl "https://stanbasetech.onrender.com/companies?country=Казахстан&industry=Technology&q=AI"

# Получение компаний на стадии Seed
curl "https://stanbasetech.onrender.com/companies?stage=Seed&per_page=50"
```

### Создание новой компании через админку
```bash
# 1. Аутентификация
curl -c cookies.txt -X POST "https://stanbasetech.onrender.com/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@example.com&password=password123"

# 2. Создание компании
curl -b cookies.txt -X POST "https://stanbasetech.onrender.com/admin/companies/create" \
  -H "Content-Type: multipart/form-data" \
  -F "name=AI Startup" \
  -F "description=Инновационная AI компания" \
  -F "country=1" \
  -F "city=1" \
  -F "industry=AI" \
  -F "status=active"
```

### Проверка состояния системы
```bash
# Проверка БД
curl "https://stanbasetech.onrender.com/test-db"

# Выполнение миграций
curl "https://stanbasetech.onrender.com/run-migration"
```

### Работа с вакансиями
```bash
# Поиск удаленных вакансий разработчика
curl "https://stanbasetech.onrender.com/jobs?q=developer&job_type=remote&city=Алматы"

# Вакансии конкретной компании
curl "https://stanbasetech.onrender.com/jobs?company=1"
```

## Интеграция

### Webhook поддержка (планируется)
```json
{
  "event": "company.created",
  "data": {
    "company_id": 123,
    "company_name": "New Company",
    "timestamp": "2024-01-15T10:00:00Z"
  }
}
```

### API версионирование (планируется)
```
/api/v1/companies
/api/v2/companies
```

### GraphQL поддержка (планируется)
```graphql
query {
  companies(country: "Казахстан") {
    id
    name
    description
    deals {
      amount
      currency
    }
  }
}
``` 