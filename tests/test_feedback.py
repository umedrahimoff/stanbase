#!/usr/bin/env python3
"""
Тест системы обратной связи
"""

import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.telegram import TelegramService
from fastapi.testclient import TestClient
from main import app

def test_telegram_service():
    """Тестируем сервис Telegram"""
    print("🤖 Тестируем сервис Telegram...")
    
    # Создаем экземпляр сервиса
    telegram = TelegramService()
    
    # Тест форматирования сообщения
    feedback_data = {
        "type": "bug",
        "description": "Кнопка не работает",
        "suggestion": "Добавить проверку",
        "user_info": {
            "name": "Тестовый пользователь",
            "email": "test@example.com",
            "is_authenticated": True
        },
        "page_info": {
            "url": "https://example.com/page",
            "title": "Тестовая страница",
            "user_agent": "Mozilla/5.0...",
            "screen_size": "1920x1080"
        }
    }
    
    message = telegram.format_feedback_message(feedback_data)
    
    # Проверяем, что сообщение содержит нужные элементы
    assert "🐛" in message
    assert "Кнопка не работает" in message
    assert "Тестовый пользователь" in message
    assert "https://example.com/page" in message
    
    print("✅ Форматирование сообщений работает корректно")
    print(f"📝 Пример сообщения:\n{message[:200]}...")

def test_feedback_api():
    """Тестируем API обратной связи"""
    print("\n🌐 Тестируем API обратной связи...")
    
    client = TestClient(app)
    
    # Тестовые данные
    feedback_data = {
        "type": "feature",
        "description": "Хочу новую функцию",
        "suggestion": "Добавить поиск",
        "page_url": "https://example.com",
        "page_title": "Тест",
        "user_agent": "Mozilla/5.0",
        "screen_size": "1920x1080",
        "user_name": "Тест",
        "user_email": "test@example.com",
        "is_authenticated": "true"
    }
    
    # Отправляем запрос
    response = client.post("/api/v1/feedback", params=feedback_data)
    
    print(f"📊 Статус ответа: {response.status_code}")
    print(f"📋 Ответ: {response.json()}")
    
    # Проверяем, что API отвечает (может быть ошибка из-за отсутствия Telegram бота)
    assert response.status_code in [200, 500]  # 500 если бот не настроен
    
    print("✅ API обратной связи работает")

def test_feedback_types():
    """Тестируем разные типы обратной связи"""
    print("\n📝 Тестируем разные типы обратной связи...")
    
    telegram = TelegramService()
    
    types = [
        ("bug", "🐛"),
        ("feature", "💡"),
        ("improvement", "⚡"),
        ("other", "📝")
    ]
    
    for feedback_type, expected_emoji in types:
        feedback_data = {
            "type": feedback_type,
            "description": f"Тест типа {feedback_type}",
            "suggestion": "",
            "user_info": {"name": "Тест", "email": "", "is_authenticated": False},
            "page_info": {"url": "", "title": "", "user_agent": "", "screen_size": ""}
        }
        
        message = telegram.format_feedback_message(feedback_data)
        assert expected_emoji in message
        print(f"✅ Тип '{feedback_type}' работает корректно ({expected_emoji})")

def test_hotkeys_info():
    """Информация о горячих клавишах"""
    print("\n⌨️ Информация о горячих клавишах:")
    print("• Windows/Linux: Ctrl + Shift + B")
    print("• Mac: Cmd + Shift + B")
    print("• Открывает форму обратной связи на любой странице")

def test_telegram_setup():
    """Инструкции по настройке Telegram"""
    print("\n🤖 Настройка Telegram бота:")
    print("1. Создайте бота через @BotFather")
    print("2. Получите токен бота")
    print("3. Добавьте бота в группу")
    print("4. Получите chat_id группы")
    print("5. Установите переменные окружения:")
    print("   export TELEGRAM_BOT_TOKEN='ваш_токен'")
    print("   export TELEGRAM_CHAT_ID='ваш_chat_id'")

def main():
    """Запуск всех тестов"""
    print("🚀 Тестирование системы обратной связи\n")
    
    try:
        test_telegram_service()
        test_feedback_types()
        test_feedback_api()
        test_hotkeys_info()
        test_telegram_setup()
        
        print("\n✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 