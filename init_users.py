#!/usr/bin/env python3
"""
Скрипт для инициализации тестовых пользователей
Запускается при первом запуске приложения
"""

from app import app, db
from models import User

def init_test_users():
    """Создает тестовых пользователей, если их еще нет"""
    with app.app_context():
        # Список тестовых пользователей
        test_users = [
            {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
            {'username': 'superadmin', 'password': 'super123', 'role': 'admin'},
            {'username': 'moderator1', 'password': 'mod123', 'role': 'moderator'},
            {'username': 'investor1', 'password': 'inv123', 'role': 'investor'},
            {'username': 'startuper1', 'password': 'start123', 'role': 'startuper'},
        ]
        
        created_count = 0
        for user_data in test_users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    username=user_data['username'],
                    password=user_data['password'],
                    role=user_data['role'],
                    status='active'
                )
                db.session.add(user)
                created_count += 1
                print(f"✅ Создан пользователь: {user_data['username']} (роль: {user_data['role']})")
            else:
                # Обновляем пароль и роль, если пользователь уже существует
                existing_user.password = user_data['password']
                existing_user.role = user_data['role']
                print(f"🔄 Обновлен пользователь: {user_data['username']} (роль: {user_data['role']})")
        
        if created_count > 0:
            db.session.commit()
            print(f"\n📊 Создано новых пользователей: {created_count}")
        
        print("\n📋 Доступные тестовые пользователи:")
        print("=" * 50)
        print("Администраторы:")
        print("  Логин: admin, Пароль: admin123")
        print("  Логин: superadmin, Пароль: super123")
        print("\nМодераторы:")
        print("  Логин: moderator1, Пароль: mod123")
        print("\nИнвесторы:")
        print("  Логин: investor1, Пароль: inv123")
        print("\nСтартаперы:")
        print("  Логин: startuper1, Пароль: start123")

if __name__ == '__main__':
    init_test_users() 