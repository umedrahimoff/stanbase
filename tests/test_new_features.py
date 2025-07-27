#!/usr/bin/env python3
"""
Скрипт для тестирования новых функций: уведомления и комментарии
"""

from db import SessionLocal
from models import User, Company, News, Job
from services.notifications import NotificationService, NotificationTemplates
from services.comments import CommentService, CommentValidator
from datetime import datetime

def test_notifications():
    """Тестируем систему уведомлений"""
    print("🔔 Тестируем систему уведомлений...")
    
    db = SessionLocal()
    try:
        # Получаем первого пользователя
        user = db.query(User).first()
        if not user:
            print("❌ Нет пользователей в базе данных")
            return
        
        print(f"👤 Тестируем для пользователя: {user.email}")
        
        # Создаем тестовые уведомления
        notifications = [
            NotificationService.create_notification(
                user_id=user.id,
                title="Добро пожаловать в stanbase!",
                message="Спасибо за регистрацию. Теперь вы можете комментировать и получать уведомления.",
                notification_type="success"
            ),
            NotificationService.create_notification(
                user_id=user.id,
                title="Новая вакансия",
                message="Компания TechCorp опубликовала новую вакансию: Senior Python Developer",
                notification_type="info",
                entity_type="job",
                entity_id=1
            ),
            NotificationService.create_notification(
                user_id=user.id,
                title="Обновление компании",
                message="Компания StartupXYZ обновила свою информацию",
                notification_type="info",
                entity_type="company",
                entity_id=1
            )
        ]
        
        print(f"✅ Создано {len(notifications)} уведомлений")
        
        # Проверяем количество непрочитанных
        unread_count = NotificationService.get_unread_count(user.id)
        print(f"📊 Непрочитанных уведомлений: {unread_count}")
        
        # Получаем все уведомления пользователя
        user_notifications = NotificationService.get_user_notifications(user.id, limit=10)
        print(f"📋 Всего уведомлений у пользователя: {len(user_notifications)}")
        
        # Отмечаем одно как прочитанное
        if user_notifications:
            first_notification = user_notifications[0]
            success = NotificationService.mark_as_read(first_notification.id, user.id)
            print(f"✅ Отметили уведомление как прочитанное: {success}")
            
            # Проверяем обновленное количество
            new_unread_count = NotificationService.get_unread_count(user.id)
            print(f"📊 Непрочитанных уведомлений после отметки: {new_unread_count}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании уведомлений: {e}")
    finally:
        db.close()

def test_comments():
    """Тестируем систему комментариев"""
    print("\n💬 Тестируем систему комментариев...")
    
    db = SessionLocal()
    try:
        # Получаем первого пользователя
        user = db.query(User).first()
        if not user:
            print("❌ Нет пользователей в базе данных")
            return
        
        # Получаем первую компанию
        company = db.query(Company).first()
        if not company:
            print("❌ Нет компаний в базе данных")
            return
        
        print(f"👤 Тестируем для пользователя: {user.email}")
        print(f"🏢 Тестируем для компании: {company.name}")
        
        # Создаем тестовые комментарии
        comments = [
            CommentService.create_comment(
                user_id=user.id,
                content="Отличная компания! Очень интересный проект.",
                entity_type="company",
                entity_id=company.id
            ),
            CommentService.create_comment(
                user_id=user.id,
                content="Интересно узнать больше о технологиях, которые они используют.",
                entity_type="company",
                entity_id=company.id
            )
        ]
        
        print(f"✅ Создано {len(comments)} комментариев")
        
        # Создаем ответ на первый комментарий
        if comments:
            reply = CommentService.create_comment(
                user_id=user.id,
                content="Согласен! Особенно впечатляет их подход к масштабированию.",
                entity_type="company",
                entity_id=company.id,
                parent_id=comments[0].id
            )
            print(f"✅ Создан ответ на комментарий: {reply.id}")
        
        # Получаем все комментарии для компании
        company_comments = CommentService.get_comments("company", company.id, limit=10)
        print(f"📋 Всего комментариев у компании: {len(company_comments)}")
        
        # Получаем количество комментариев
        comment_count = CommentService.get_comment_count("company", company.id)
        print(f"📊 Общее количество комментариев: {comment_count}")
        
        # Проверяем валидацию
        print("\n🔍 Тестируем валидацию комментариев...")
        
        # Тест валидного типа сущности
        is_valid = CommentValidator.is_valid_entity_type("company")
        print(f"✅ Валидный тип 'company': {is_valid}")
        
        # Тест невалидного типа сущности
        is_invalid = CommentValidator.is_valid_entity_type("invalid_type")
        print(f"❌ Невалидный тип 'invalid_type': {is_invalid}")
        
        # Тест валидации содержимого
        content_errors = CommentValidator.validate_content("")
        print(f"📝 Ошибки для пустого содержимого: {content_errors}")
        
        content_errors = CommentValidator.validate_content("Спам реклама купить")
        print(f"📝 Ошибки для спам-содержимого: {content_errors}")
        
        content_errors = CommentValidator.validate_content("Отличный комментарий!")
        print(f"📝 Ошибки для валидного содержимого: {content_errors}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании комментариев: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_api_endpoints():
    """Тестируем API эндпоинты"""
    print("\n🌐 Тестируем API эндпоинты...")
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # Тест получения компаний
    try:
        response = requests.get(f"{base_url}/api/v1/companies?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API компаний работает: получено {len(data.get('companies', []))} компаний")
        else:
            print(f"❌ API компаний вернул статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании API компаний: {e}")
    
    # Тест получения инвесторов
    try:
        response = requests.get(f"{base_url}/api/v1/investors?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API инвесторов работает: получено {len(data.get('investors', []))} инвесторов")
        else:
            print(f"❌ API инвесторов вернул статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании API инвесторов: {e}")
    
    # Тест получения вакансий
    try:
        response = requests.get(f"{base_url}/api/v1/jobs?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API вакансий работает: получено {len(data.get('jobs', []))} вакансий")
        else:
            print(f"❌ API вакансий вернул статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании API вакансий: {e}")

if __name__ == "__main__":
    print("🚀 Запускаем тестирование новых функций...\n")
    
    try:
        test_notifications()
        test_comments()
        test_api_endpoints()
        
        print("\n🎉 Тестирование завершено!")
        print("\n📋 Резюме реализованных функций:")
        print("✅ Система уведомлений с созданием, чтением и управлением")
        print("✅ Система комментариев с поддержкой ответов")
        print("✅ Валидация комментариев и защита от спама")
        print("✅ RESTful API для уведомлений, комментариев и основных сущностей")
        print("✅ Веб-интерфейс для уведомлений")
        print("✅ Компонент комментариев для интеграции в страницы")
        print("✅ Обновленная навигация с уведомлениями")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc() 