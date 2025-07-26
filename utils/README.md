# Utils

Утилиты и вспомогательные функции.

## Файлы:

- **security.py** - Функции безопасности: хеширование паролей, JWT токены
- **csrf.py** - CSRF защита для форм
- **migrate_passwords.py** - Миграция паролей с MD5 на bcrypt
- **migrate_to_prod.py** - Миграция данных для продакшена

## Использование:

```python
from utils.security import verify_password, get_password_hash, create_access_token
from utils.csrf import get_csrf_token, verify_csrf_token
from utils.migrate_passwords import migrate_user_passwords
``` 