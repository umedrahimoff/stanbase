# Настройка системы почты

## Обзор

Система почты в Stanbase позволяет отправлять:
- Приветственные письма при регистрации
- Письма для восстановления пароля
- Уведомления об обратной связи
- Общие уведомления пользователям

## Зависимости

Добавлены новые зависимости в `requirements.txt`:
```
fastapi-mail
python-dotenv
```

## Конфигурация

### Переменные окружения

Добавьте следующие переменные в файл `.env`:

```env
# Email Configuration
MAIL_USERNAME=noreply@stanbase.tech
MAIL_PASSWORD=your_email_password_here
MAIL_FROM=noreply@stanbase.tech
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=Stanbase

# Site Configuration
SITE_URL=https://stanbase.tech
ADMIN_EMAILS=admin@stanbase.tech,manager@stanbase.tech
```

### Настройка Gmail

Для использования Gmail в качестве SMTP сервера:

1. Включите двухфакторную аутентификацию в Google аккаунте
2. Создайте пароль приложения:
   - Перейдите в настройки безопасности Google
   - Выберите "Пароли приложений"
   - Создайте новый пароль для "Почта"
   - Используйте этот пароль в `MAIL_PASSWORD`

### Альтернативные SMTP серверы

#### Yandex
```env
MAIL_SERVER=smtp.yandex.ru
MAIL_PORT=465
MAIL_SSL=True
MAIL_TLS=False
```

#### Mail.ru
```env
MAIL_SERVER=smtp.mail.ru
MAIL_PORT=465
MAIL_SSL=True
MAIL_TLS=False
```

## Структура файлов

### Сервис почты
- `services/email.py` - основной сервис для отправки писем

### Шаблоны писем
- `templates/emails/base.html` - базовый шаблон для всех писем
- `templates/emails/welcome.html` - приветственное письмо
- `templates/emails/password_reset.html` - восстановление пароля
- `templates/emails/email_verification.html` - подтверждение email
- `templates/emails/notification.html` - общие уведомления
- `templates/emails/feedback_notification.html` - уведомления об обратной связи

### Страницы восстановления пароля
- `templates/auth/forgot_password.html` - запрос восстановления
- `templates/auth/reset_password.html` - создание нового пароля

## API

### EmailService

Основной класс для работы с почтой:

```python
from services.email import email_service

# Приветственное письмо
await email_service.send_welcome_email(user_email, user_name)

# Восстановление пароля
await email_service.send_password_reset_email(user_email, reset_token)

# Подтверждение email
await email_service.send_email_verification(user_email, verification_token)

# Общее уведомление
await email_service.send_notification_email(user_email, subject, message)

# Уведомление об обратной связи
await email_service.send_feedback_notification(feedback_data)
```

## Маршруты

### Восстановление пароля
- `GET /forgot-password` - страница запроса восстановления
- `POST /forgot-password` - обработка запроса
- `GET /reset-password?token=...` - страница сброса пароля
- `POST /reset-password` - обработка сброса пароля

## Интеграция

### Регистрация
При успешной регистрации автоматически отправляется приветственное письмо.

### Обратная связь
При получении новой обратной связи отправляется уведомление администраторам.

### Восстановление пароля
Пользователи могут запросить восстановление пароля через форму входа.

## Безопасность

1. **Токены**: Для восстановления пароля используются криптографически стойкие токены
2. **Валидация**: Все email адреса валидируются перед отправкой
3. **Логирование**: Ошибки отправки логируются для отладки
4. **Rate Limiting**: Рекомендуется добавить ограничение на количество запросов

## Тестирование

### Локальное тестирование
Для тестирования без реальной отправки можно использовать:
- MailHog
- Mailtrap
- Локальный SMTP сервер

### Пример конфигурации для тестирования
```env
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_SSL=False
MAIL_TLS=False
```

## Мониторинг

### Логи
Все ошибки отправки логируются в консоль:
```
Ошибка отправки приветственного письма: [error details]
Ошибка отправки email уведомления: [error details]
```

### Метрики
Рекомендуется добавить метрики для:
- Количества отправленных писем
- Процента доставки
- Времени доставки
- Ошибок отправки

## Устранение неполадок

### Частые проблемы

1. **Ошибка аутентификации**
   - Проверьте правильность логина и пароля
   - Убедитесь, что включена двухфакторная аутентификация
   - Используйте пароль приложения для Gmail

2. **Письма не отправляются**
   - Проверьте настройки SMTP сервера
   - Убедитесь, что порт не заблокирован
   - Проверьте логи на наличие ошибок

3. **Письма попадают в спам**
   - Настройте SPF, DKIM и DMARC записи
   - Используйте правильный обратный адрес
   - Избегайте спам-триггеров в тексте

### Отладка
Включите подробное логирование:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Расширение

### Добавление новых типов писем
1. Создайте шаблон в `templates/emails/`
2. Добавьте метод в `EmailService`
3. Интегрируйте в соответствующий функционал

### Кастомизация шаблонов
Все шаблоны используют базовый шаблон `base.html` с фирменным стилем Stanbase. 