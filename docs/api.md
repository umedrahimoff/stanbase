# API

## Обзор

Stanbase предоставляет REST API для работы с данными компаний, инвесторов и связанных сущностей.

## Базовый URL

```
https://stanbasetech.onrender.com
```

## Аутентификация

API использует сессионную аутентификацию. Для доступа к защищенным эндпоинтам требуется авторизация.

## Основные эндпоинты

### 🏠 Главная страница

**GET /** - Главная страница с обзором данных

**Ответ:** HTML страница с карточками компаний, инвесторов, новостей

### 🏢 Компании

**GET /companies** - Каталог компаний

**Параметры:**
- `q` (string) - поисковый запрос
- `country` (string) - фильтр по стране
- `stage` (string) - фильтр по стадии
- `industry` (string) - фильтр по отрасли

**Ответ:** HTML страница со списком компаний

---

**GET /company/{id}** - Детальная страница компании

**Параметры:**
- `id` (integer) - ID компании

**Ответ:** HTML страница с полной информацией о компании

### 💰 Инвесторы

**GET /investors** - Каталог инвесторов

**Параметры:**
- `q` (string) - поисковый запрос
- `country` (string) - фильтр по стране
- `focus` (string) - фильтр по фокусу
- `stages` (string) - фильтр по стадиям

**Ответ:** HTML страница со списком инвесторов

---

**GET /investor/{id}** - Детальная страница инвестора

**Параметры:**
- `id` (integer) - ID инвестора

**Ответ:** HTML страница с полной информацией об инвесторе

### 💼 Вакансии

**GET /jobs** - Список вакансий

**Параметры:**
- `q` (string) - поисковый запрос
- `city` (string) - фильтр по городу
- `job_type` (string) - фильтр по типу работы
- `company` (integer) - фильтр по компании

**Ответ:** HTML страница со списком вакансий

---

**GET /job/{id}** - Детальная страница вакансии

**Параметры:**
- `id` (integer) - ID вакансии

**Ответ:** HTML страница с полной информацией о вакансии

### 📰 Новости и события

**GET /news** - Список новостей

**Ответ:** HTML страница со списком новостей

---

**GET /news/{id}** - Детальная страница новости

**Параметры:**
- `id` (integer) - ID новости

**Ответ:** HTML страница с полной новостью

---

**GET /events** - Список событий

**Ответ:** HTML страница со списком событий

---

**GET /event/{id}** - Детальная страница события

**Параметры:**
- `id` (integer) - ID события

**Ответ:** HTML страница с полной информацией о событии

## Админ API

### 🔐 Аутентификация

**POST /login** - Вход в систему

**Параметры:**
- `email` (string) - email пользователя
- `password` (string) - пароль

**Ответ:** Redirect на админ-панель или ошибка

---

**GET /logout** - Выход из системы

**Ответ:** Redirect на главную страницу

### 📊 Админ-панель

**GET /admin** - Главная страница админки

**Ответ:** HTML страница с дашбордом

### 🏢 Управление компаниями

**GET /admin/companies** - Список компаний

**Параметры:**
- `q` (string) - поиск
- `status` (string) - фильтр по статусу
- `page` (integer) - номер страницы
- `per_page` (integer) - элементов на странице

---

**GET /admin/companies/create** - Форма создания компании

---

**POST /admin/companies/create** - Создание компании

**Параметры:**
- `name` (string) - название
- `description` (string) - описание
- `country` (integer) - ID страны
- `city` (integer) - ID города
- `status` (string) - статус
- `founded_date` (date) - дата основания
- `website` (string) - веб-сайт
- `logo` (file) - логотип

---

**GET /admin/companies/edit/{id}** - Форма редактирования

---

**POST /admin/companies/edit/{id}** - Обновление компании

---

**POST /admin/companies/delete/{id}** - Удаление компании

### 💰 Управление инвесторами

**GET /admin/investors** - Список инвесторов

**GET /admin/investors/create** - Форма создания

**POST /admin/investors/create** - Создание инвестора

**GET /admin/investors/edit/{id}** - Форма редактирования

**POST /admin/investors/edit/{id}** - Обновление инвестора

**POST /admin/investors/delete/{id}` - Удаление инвестора

### 💼 Управление вакансиями

**GET /admin/jobs** - Список вакансий

**GET /admin/jobs/create** - Форма создания

**POST /admin/jobs/create** - Создание вакансии

**GET /admin/jobs/edit/{id}` - Форма редактирования

**POST /admin/jobs/edit/{id}` - Обновление вакансии

**POST /admin/jobs/delete/{id}` - Удаление вакансии

### 📰 Управление контентом

**GET /admin/news** - Список новостей

**GET /admin/events** - Список событий

**GET /admin/podcasts** - Список подкастов

### 🔧 Системные эндпоинты

**GET /run-migration** - Выполнение миграций БД

**Ответ:** JSON с результатом миграции

---

**POST /import-data** - Импорт данных

**Параметры:**
- `data` (object) - данные для импорта

**Ответ:** JSON с результатом импорта

---

**GET /test-db** - Тестирование состояния БД

**Ответ:** JSON с информацией о БД

## Обработка ошибок

### HTTP статусы

- `200` - Успешный запрос
- `302` - Redirect
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
```

## Примеры запросов

### Поиск компаний

```bash
curl "https://stanbasetech.onrender.com/companies?q=tech&country=Казахстан"
```

### Получение детальной информации

```bash
curl "https://stanbasetech.onrender.com/company/1"
```

### Создание компании (требует авторизации)

```bash
curl -X POST "https://stanbasetech.onrender.com/admin/companies/create" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Test Company&description=Test description&country=1&city=1&status=active"
``` 