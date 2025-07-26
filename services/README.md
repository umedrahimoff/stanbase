# Services

Сервисы для бизнес-логики приложения.

## Файлы:

- **api.py** - REST API роуты для уведомлений, комментариев, компаний, инвесторов, вакансий и управления кешем
- **cache.py** - Система кеширования с файловым хранилищем, TTL и автоматической инвалидацией
- **pagination.py** - Система пагинации для эффективной работы с большими наборами данных
- **comments.py** - Сервис для работы с комментариями и ответами
- **notifications.py** - Сервис для работы с уведомлениями пользователей

## Использование:

```python
from services.api import api_router
from services.cache import QueryCache, CacheInvalidator
from services.pagination import PaginationHelper, DatabasePagination
from services.comments import CommentService
from services.notifications import NotificationService
``` 