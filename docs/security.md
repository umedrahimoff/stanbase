# Безопасность

## Реализованные меры защиты

### 🔐 Хеширование паролей

**Проблема:** Пароли хранились в открытом виде в базе данных.

**Решение:** Использование bcrypt для хеширования паролей.

```python
from security import get_password_hash, verify_password

# При создании пользователя
user.password = get_password_hash(plain_password)

# При проверке пароля
if verify_password(plain_password, user.password):
    # Пароль верный
```

**Преимущества:**
- Пароли никогда не хранятся в открытом виде
- bcrypt автоматически добавляет соль
- Адаптивный алгоритм (можно увеличивать сложность)

### 🎫 JWT токены

**Проблема:** Отсутствие безопасной аутентификации для API.

**Решение:** JWT токены для API аутентификации.

```python
from security import create_access_token, verify_token

# Создание токена
token = create_access_token(data={"sub": user.email, "role": user.role})

# Проверка токена
payload = verify_token(token)
if payload:
    user_email = payload.get("sub")
```

**Настройки:**
- Алгоритм: HS256
- Время жизни: 30 минут
- Секретный ключ: настраивается через переменную окружения

### 🛡️ CSRF защита

**Проблема:** Отсутствие защиты от Cross-Site Request Forgery атак.

**Решение:** CSRF токены для всех POST запросов.

```python
from csrf import get_csrf_token, verify_csrf_token

# Генерация токена
token = get_csrf_token(request)

# Проверка токена
if verify_csrf_token(request, token):
    # Запрос безопасен
```

**Особенности:**
- Токены привязаны к пользователю и сессии
- Время жизни: 1 час
- Автоматическая генерация session_id

### 🔒 Улучшенная аутентификация

**Изменения в системе входа:**

1. **Проверка хешированных паролей:**
```python
# Старый код
user = db.query(User).filter_by(email=email, password=password).first()

# Новый код
user = db.query(User).filter_by(email=email).first()
if user and verify_password(password, user.password):
    # Пользователь аутентифицирован
```

2. **Безопасное хранение в сессии:**
```python
request.session["user_id"] = user.id
request.session["role"] = user.role
request.session["user_email"] = user.email
request.session["user_name"] = user.first_name
```

## Миграция данных

### Скрипт миграции паролей

Для обновления существующих паролей в базе данных:

```bash
python migrate_passwords.py
```

Скрипт:
1. Находит все нехешированные пароли
2. Конвертирует их в bcrypt хеши
3. Проверяет результат миграции

### Проверка миграции

```python
from migrate_passwords import verify_migration
verify_migration()
```

## Переменные окружения

### Обязательные переменные

```bash
# Секретный ключ для JWT токенов (измените в продакшене!)
SECRET_KEY=your_super_secret_key_here

# Секретный ключ для сессий
SESSION_SECRET_KEY=your_session_secret_key_here
```

### Рекомендуемые настройки

```bash
# Время жизни JWT токенов (в минутах)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Время жизни CSRF токенов (в секундах)
CSRF_TOKEN_MAX_AGE=3600
```

## Рекомендации по безопасности

### 🔐 Пароли

1. **Минимальная длина:** 8 символов
2. **Сложность:** буквы, цифры, специальные символы
3. **Политика:** не использовать повторно пароли

### 🛡️ Сессии

1. **Время жизни:** настраивается в зависимости от требований
2. **HTTPS:** обязательно в продакшене
3. **HttpOnly cookies:** для защиты от XSS

### 🔍 Мониторинг

1. **Логирование:** всех попыток входа
2. **Алерты:** при подозрительной активности
3. **Аудит:** регулярные проверки безопасности

## Тестирование безопасности

### Проверка хеширования

```python
from security import get_password_hash, verify_password

# Тест хеширования
password = "test123"
hashed = get_password_hash(password)
assert verify_password(password, hashed) == True
assert verify_password("wrong", hashed) == False
```

### Проверка CSRF защиты

```python
from csrf import get_csrf_token, verify_csrf_token

# Тест CSRF токенов
token = get_csrf_token(request)
assert verify_csrf_token(request, token) == True
assert verify_csrf_token(request, "fake_token") == False
```

## Обновления безопасности

### Версия 1.1.0
- ✅ Хеширование паролей с bcrypt
- ✅ JWT токены для API
- ✅ CSRF защита
- ✅ Улучшенная аутентификация
- ✅ Скрипт миграции паролей

### Планируемые улучшения
- [ ] Rate limiting для API
- [ ] Двухфакторная аутентификация
- [ ] Аудит действий пользователей
- [ ] Автоматическое обновление паролей
- [ ] Интеграция с внешними провайдерами аутентификации 