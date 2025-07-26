# Новые функции StanBase

## 🎯 Обзор

В этой версии добавлены следующие новые функции:
- **Система уведомлений** - для информирования пользователей о важных событиях
- **Система комментариев** - для обсуждения компаний, инвесторов, новостей и вакансий
- **RESTful API** - для интеграции с внешними системами

## 🔔 Система уведомлений

### Возможности
- Создание уведомлений для пользователей
- Отметка уведомлений как прочитанных
- Удаление уведомлений
- Подсчет непрочитанных уведомлений
- Различные типы уведомлений (info, success, warning, error)

### Веб-интерфейс
- Страница `/notifications` - список всех уведомлений пользователя
- Возможность отметить все уведомления как прочитанные
- Удаление отдельных уведомлений
- Счетчик непрочитанных уведомлений в навигации

### API эндпоинты
```
GET /api/v1/notifications?token=...&limit=20&unread_only=false
POST /api/v1/notifications/{notification_id}/read?token=...
POST /api/v1/notifications/read-all?token=...
GET /api/v1/notifications/unread-count?token=...
```

### Примеры использования

#### Создание уведомления
```python
from notifications import NotificationService

# Создание простого уведомления
notification = NotificationService.create_notification(
    user_id=123,
    title="Новое уведомление",
    message="Текст уведомления",
    notification_type="info"
)

# Создание уведомления с привязкой к сущности
notification = NotificationService.create_notification(
    user_id=123,
    title="Новая вакансия",
    message="Опубликована новая вакансия",
    notification_type="success",
    entity_type="job",
    entity_id=456
)
```

#### Использование шаблонов
```python
from notifications import NotificationTemplates

# Уведомление о новом комментарии
template = NotificationTemplates.new_comment("компании", "TechCorp")
notification = NotificationService.create_notification(
    user_id=123,
    **template
)
```

## 💬 Система комментариев

### Возможности
- Добавление комментариев к различным сущностям
- Поддержка ответов на комментарии (вложенные комментарии)
- Валидация содержимого комментариев
- Защита от спама
- Удаление комментариев (мягкое удаление)

### Поддерживаемые типы сущностей
- `company` - компании
- `investor` - инвесторы
- `news` - новости
- `job` - вакансии
- `event` - мероприятия

### Веб-компонент
Компонент `templates/components/comments.html` можно включить в любую страницу:

```html
{% include "components/comments.html" with context %}
```

### API эндпоинты
```
GET /api/v1/comments/{entity_type}/{entity_id}?limit=50&offset=0
POST /api/v1/comments?token=...&entity_type=...&entity_id=...&content=...&parent_id=...
PUT /api/v1/comments/{comment_id}?token=...&content=...
DELETE /api/v1/comments/{comment_id}?token=...
```

### Примеры использования

#### Создание комментария
```python
from comments import CommentService, CommentValidator

# Валидация содержимого
errors = CommentValidator.validate_content("Текст комментария")
if errors:
    print(f"Ошибки валидации: {errors}")

# Создание комментария
comment = CommentService.create_comment(
    user_id=123,
    content="Отличная компания!",
    entity_type="company",
    entity_id=456
)

# Создание ответа на комментарий
reply = CommentService.create_comment(
    user_id=123,
    content="Согласен!",
    entity_type="company",
    entity_id=456,
    parent_id=comment.id
)
```

#### Получение комментариев
```python
# Получение комментариев для компании
comments = CommentService.get_comments("company", 456, limit=20)

# Получение ответов на комментарий
replies = CommentService.get_replies(comment.id)

# Подсчет комментариев
count = CommentService.get_comment_count("company", 456)
```

## 🌐 RESTful API

### Общие принципы
- Все API эндпоинты начинаются с `/api/v1/`
- Аутентификация через JWT токены
- Стандартные HTTP методы (GET, POST, PUT, DELETE)
- JSON формат данных
- Пагинация через параметры `limit` и `offset`

### Аутентификация
Для защищенных эндпоинтов требуется токен:
```
?token=your_jwt_token_here
```

### Основные эндпоинты

#### Компании
```
GET /api/v1/companies?limit=20&offset=0&country=KZ&stage=seed&industry=tech
GET /api/v1/companies/{company_id}
```

#### Инвесторы
```
GET /api/v1/investors?limit=20&offset=0&country=KZ&focus=tech
```

#### Вакансии
```
GET /api/v1/jobs?limit=20&offset=0&city=Almaty&job_type=fulltime
```

### Примеры ответов

#### Список компаний
```json
{
  "success": true,
  "companies": [
    {
      "id": 1,
      "name": "TechCorp",
      "description": "Описание компании",
      "country": "KZ",
      "city": "Almaty",
      "stage": "seed",
      "industry": "tech",
      "website": "https://techcorp.com",
      "founded_date": "2023-01-01"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

#### Комментарии
```json
{
  "success": true,
  "comments": [
    {
      "id": 1,
      "content": "Отличная компания!",
      "user": {
        "id": 123,
        "name": "Иван Иванов",
        "email": "ivan@example.com"
      },
      "created_at": "2024-01-15T10:30:00",
      "replies": [
        {
          "id": 2,
          "content": "Согласен!",
          "user": {
            "id": 124,
            "name": "Петр Петров",
            "email": "petr@example.com"
          },
          "created_at": "2024-01-15T11:00:00"
        }
      ]
    }
  ],
  "total": 5
}
```

## 🔧 Интеграция в существующие страницы

### Добавление комментариев на страницу компании

В шаблоне `templates/public/companies/detail.html`:

```html
<!-- В конце страницы -->
{% include "components/comments.html" with context %}
```

В роуте `company_detail`:

```python
from comments import CommentService

@app.get("/companies/{company_id}")
async def company_detail(request: Request, company_id: int):
    # ... существующий код ...
    
    # Получаем комментарии для компании
    comments = CommentService.get_comments("company", company_id, limit=50)
    
    return templates.TemplateResponse("public/companies/detail.html", {
        "request": request,
        "company": company,
        "comments": comments,  # Добавляем комментарии
        "entity_type": "company",  # Для компонента комментариев
        "entity_id": company_id,   # Для компонента комментариев
        "session": request.session
    })
```

### Добавление уведомлений в навигацию

В `templates/layout.html` уже добавлена ссылка на уведомления в выпадающем меню пользователя.

## 🧪 Тестирование

Для тестирования новых функций используйте скрипт `test_new_features.py`:

```bash
python3 test_new_features.py
```

Этот скрипт:
- Создает тестовые уведомления
- Создает тестовые комментарии
- Проверяет валидацию
- Тестирует API эндпоинты

## 📊 База данных

### Новые таблицы

#### `notification`
- `id` - первичный ключ
- `user_id` - ID пользователя
- `title` - заголовок уведомления
- `message` - текст уведомления
- `type` - тип уведомления (info, success, warning, error)
- `entity_type` - тип связанной сущности
- `entity_id` - ID связанной сущности
- `is_read` - прочитано ли уведомление
- `created_at` - дата создания

#### `comment`
- `id` - первичный ключ
- `content` - содержимое комментария
- `user_id` - ID пользователя
- `entity_type` - тип сущности
- `entity_id` - ID сущности
- `parent_id` - ID родительского комментария (для ответов)
- `status` - статус комментария (active, deleted)
- `created_at` - дата создания
- `updated_at` - дата обновления

#### `user_activity`
- `id` - первичный ключ
- `user_id` - ID пользователя
- `action` - действие (login, logout, create, update, delete)
- `entity_type` - тип сущности
- `entity_id` - ID сущности
- `ip_address` - IP адрес
- `user_agent` - User Agent
- `created_at` - дата создания

## 🚀 Развертывание

1. Обновите базу данных:
```bash
python3 init_db.py
```

2. Запустите приложение:
```bash
python3 main.py
```

3. Проверьте работу новых функций:
- Откройте http://localhost:8000
- Войдите в систему
- Проверьте страницу уведомлений: http://localhost:8000/notifications
- Добавьте комментарии на страницах компаний

## 🔮 Планы развития

- [ ] Email уведомления
- [ ] Push уведомления
- [ ] Модерация комментариев
- [ ] Рейтинг комментариев
- [ ] Уведомления в реальном времени (WebSocket)
- [ ] API для мобильного приложения
- [ ] Экспорт данных через API 