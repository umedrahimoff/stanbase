#!/usr/bin/env python3
"""
Тест функций безопасности
"""

from utils.security import get_password_hash, verify_password, create_access_token, verify_token
from utils.csrf import get_csrf_token, verify_csrf_token, CSRFProtection
import time

def test_password_hashing():
    """Тест хеширования паролей"""
    print("🔐 Тестируем хеширование паролей...")
    
    password = "test123"
    hashed = get_password_hash(password)
    
    print(f"Пароль: {password}")
    print(f"Хеш: {hashed}")
    print(f"Длина хеша: {len(hashed)}")
    print(f"Начинается с $2b$: {hashed.startswith('$2b$')}")
    
    # Проверяем правильный пароль
    assert verify_password(password, hashed) == True
    print("✅ Правильный пароль проверяется корректно")
    
    # Проверяем неправильный пароль
    assert verify_password("wrong", hashed) == False
    print("✅ Неправильный пароль отклоняется корректно")
    
    print("✅ Тест хеширования паролей пройден\n")

def test_jwt_tokens():
    """Тест JWT токенов"""
    print("🎫 Тестируем JWT токены...")
    
    data = {"sub": "test@example.com", "role": "admin"}
    token = create_access_token(data)
    
    print(f"Данные: {data}")
    print(f"Токен: {token[:50]}...")
    
    # Проверяем токен
    payload = verify_token(token)
    assert payload is not None
    assert payload.get("sub") == "test@example.com"
    assert payload.get("role") == "admin"
    print("✅ JWT токен создается и проверяется корректно")
    
    # Проверяем неверный токен
    fake_payload = verify_token("fake_token")
    assert fake_payload is None
    print("✅ Неверный токен отклоняется корректно")
    
    print("✅ Тест JWT токенов пройден\n")

def test_csrf_protection():
    """Тест CSRF защиты"""
    print("🛡️ Тестируем CSRF защиту...")
    
    csrf = CSRFProtection()
    user_id = 123
    session_id = "test_session_123"
    
    # Генерируем токен
    token = csrf.generate_token(user_id, session_id)
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print(f"CSRF токен: {token}")
    
    # Проверяем токен
    assert csrf.verify_token(token, user_id, session_id) == True
    print("✅ CSRF токен проверяется корректно")
    
    # Проверяем неверный токен
    assert csrf.verify_token("fake_token", user_id, session_id) == False
    print("✅ Неверный CSRF токен отклоняется корректно")
    
    # Проверяем токен с неверными данными
    assert csrf.verify_token(token, 999, session_id) == False
    print("✅ CSRF токен с неверным user_id отклоняется корректно")
    
    print("✅ Тест CSRF защиты пройден\n")

def test_password_migration():
    """Тест миграции паролей"""
    print("🔄 Тестируем миграцию паролей...")
    
    from utils.migrate_passwords import is_hashed_password
    
    # Тест нехешированного пароля
    plain_password = "test123"
    assert is_hashed_password(plain_password) == False
    print("✅ Нехешированный пароль определяется корректно")
    
    # Тест хешированного пароля
    hashed_password = get_password_hash(plain_password)
    assert is_hashed_password(hashed_password) == True
    print("✅ Хешированный пароль определяется корректно")
    
    print("✅ Тест миграции паролей пройден\n")

if __name__ == "__main__":
    print("🚀 Запускаем тесты безопасности...\n")
    
    try:
        test_password_hashing()
        test_jwt_tokens()
        test_csrf_protection()
        test_password_migration()
        
        print("🎉 Все тесты безопасности пройдены успешно!")
        print("\n📋 Резюме реализованных мер безопасности:")
        print("✅ Хеширование паролей с bcrypt")
        print("✅ JWT токены для API аутентификации")
        print("✅ CSRF защита от межсайтовых запросов")
        print("✅ Скрипт миграции существующих паролей")
        print("✅ Улучшенная система аутентификации")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc() 