# Тестовые данные для Stanbase

## Проблема решена! ✅

**Проблема**: При каждом перезапуске приложения автоматически создавались тестовые данные, что приводило к дублированию записей.

**Решение**: Тестовые данные теперь создаются только по запросу через отдельный скрипт, а в продакшене создание тестовых данных полностью запрещено.

## Переменные окружения

### ENVIRONMENT
Управляет поведением создания данных:

- `ENVIRONMENT=development` (по умолчанию) - разрешено создание тестовых данных
- `ENVIRONMENT=staging` - разрешено создание тестовых данных  
- `ENVIRONMENT=production` - **запрещено** создание тестовых данных

## Как использовать

### 1. Создание тестовых данных (только в development/staging)

```bash
# Development (по умолчанию)
python init_test_data.py

# Staging
ENVIRONMENT=staging python init_test_data.py

# Production - БУДЕТ ОШИБКА!
ENVIRONMENT=production python init_test_data.py
# ❌ ОШИБКА: Создание тестовых данных запрещено в продакшене!
```

Этот скрипт создаст:
- Страны (Казахстан, Узбекистан, Кыргызстан, Таджикистан, Туркменистан)
- Города (Алматы, Астана, Ташкент, Бишкек, Душанбе)
- Категории (Fintech, HealthTech, HRTech, E-commerce, SaaS)
- Компании (CerebraAI, Uzum, Tezbus, Voicy, FORBOSSINFO, Pamir Group, BILLZ)
- Новости (6 новостей о стартапах ЦА)
- Тестовых пользователей:
  - `admin@stanbase.test` / `admin123` (администратор)
  - `moderator@stanbase.test` / `mod123` (модератор)
  - `startuper@stanbase.test` / `startuper123` (стартапер)
- Email шаблоны (приветствие, сброс пароля)

### 2. Обычный запуск приложения

```bash
# Development
python main.py

# Staging  
ENVIRONMENT=staging python main.py

# Production
ENVIRONMENT=production python main.py
```

Теперь при запуске приложения тестовые данные **НЕ** создаются автоматически.

### 3. Инициализация структуры БД

```bash
# Development - создаст структуру + тестовые данные
python init_db.py

# Staging - создаст структуру + тестовые данные
ENVIRONMENT=staging python init_db.py

# Production - создаст ТОЛЬКО структуру и email шаблоны
ENVIRONMENT=production python init_db.py
```

## Что изменилось

### В `main.py`:
- ❌ Удален автоматический вызов `create_full_test_data()`
- ✅ Функция `create_full_test_data()` осталась для возможного использования в будущем
- ✅ Создание таблиц (`Base.metadata.create_all()`) осталось

### В `init_test_data.py`:
- ✅ Добавлена проверка `ENVIRONMENT=production`
- ✅ Запрет создания тестовых данных в продакшене
- ✅ Информативные сообщения об ошибках

### В `init_db.py`:
- ✅ Добавлена проверка `ENVIRONMENT=production`
- ✅ В продакшене создаются только структуры таблиц и email шаблоны
- ✅ Тестовые данные создаются только в development/staging

### В `config.py`:
- ✅ Добавлены переменные `ENVIRONMENT`, `IS_PRODUCTION`, `IS_DEVELOPMENT`, `IS_STAGING`

### Новые файлы:
- ✅ `init_test_data.py` - скрипт для создания тестовых данных
- ✅ `README_TEST_DATA.md` - эта инструкция

## Логин для тестирования

После создания тестовых данных используйте:

| Email | Пароль | Роль |
|-------|--------|------|
| `admin@stanbase.test` | `admin123` | Администратор |
| `moderator@stanbase.test` | `mod123` | Модератор |
| `startuper@stanbase.test` | `startuper123` | Стартапер |

## Безопасность

- ✅ Тестовые данные создаются только если соответствующие таблицы пусты
- ✅ Скрипт можно запускать многократно без дублирования данных
- ✅ **В продакшене создание тестовых данных полностью запрещено**
- ✅ В продакшене создаются только структуры таблиц и email шаблоны
- ✅ Переменная `ENVIRONMENT=production` защищает от случайного создания тестовых данных

## Примеры использования

### Development (локальная разработка)
```bash
# Создать тестовые данные
python init_test_data.py

# Запустить приложение
python main.py
```

### Staging (тестовая среда)
```bash
# Создать тестовые данные
ENVIRONMENT=staging python init_test_data.py

# Запустить приложение
ENVIRONMENT=staging python main.py
```

### Production (продакшен)
```bash
# Создать только структуру БД (без тестовых данных)
ENVIRONMENT=production python init_db.py

# Запустить приложение
ENVIRONMENT=production python main.py
```