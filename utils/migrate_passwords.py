#!/usr/bin/env python3
"""
Скрипт для миграции паролей в базе данных.
Конвертирует открытые пароли в хешированные версии.
"""

from db import SessionLocal
from models import User
from security import get_password_hash, verify_password
import re

def is_hashed_password(password):
    """Проверяет, является ли пароль уже хешированным"""
    # bcrypt хеши начинаются с $2b$ и имеют длину 60 символов
    return password.startswith('$2b$') and len(password) == 60

def migrate_passwords():
    """Мигрирует все открытые пароли в хешированные"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        migrated_count = 0
        
        for user in users:
            if not is_hashed_password(user.password):
                print(f"Мигрируем пароль для пользователя {user.email}")
                # Хешируем пароль
                user.password = get_password_hash(user.password)
                migrated_count += 1
        
        if migrated_count > 0:
            db.commit()
            print(f"Успешно мигрировано {migrated_count} паролей")
        else:
            print("Все пароли уже хешированы")
            
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        db.rollback()
    finally:
        db.close()

def verify_migration():
    """Проверяет, что все пароли хешированы"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        unhashed_count = 0
        
        for user in users:
            if not is_hashed_password(user.password):
                print(f"Пароль пользователя {user.email} не хеширован")
                unhashed_count += 1
        
        if unhashed_count == 0:
            print("✅ Все пароли успешно хешированы")
        else:
            print(f"❌ Найдено {unhashed_count} нехешированных паролей")
            
    except Exception as e:
        print(f"Ошибка при проверке: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Начинаем миграцию паролей...")
    migrate_passwords()
    print("\nПроверяем результат миграции...")
    verify_migration() 