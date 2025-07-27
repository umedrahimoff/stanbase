"""
Сервис для отправки сообщений в Telegram группу
"""

import aiohttp
import json
from typing import Optional, Dict, Any
from datetime import datetime
import os

class TelegramService:
    """Сервис для работы с Telegram Bot API"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        # Импортируем конфигурацию
        try:
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
            self.chat_id = chat_id or TELEGRAM_CHAT_ID
        except ImportError:
            # Fallback к переменным окружения
            self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN', '')
            self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID', '')
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        """Отправляет сообщение в Telegram группу"""
        if not self.bot_token or not self.chat_id:
            return {"success": False, "error": "Telegram bot not configured"}
        
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            # Создаем SSL контекст для обхода проблем с сертификатами
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    return {"success": response.status == 200, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def format_feedback_message(self, feedback_data: Dict[str, Any]) -> str:
        """Форматирует сообщение обратной связи для Telegram"""
        user_info = feedback_data.get('user_info', {})
        page_info = feedback_data.get('page_info', {})
        
        # Эмодзи для разных типов обратной связи
        emoji_map = {
            'bug': '🐛',
            'feature': '💡', 
            'improvement': '⚡',
            'other': '📝'
        }
        
        feedback_type = feedback_data.get('type', 'other')
        emoji = emoji_map.get(feedback_type, '📝')
        
        message = f"""
{emoji} <b>Новое сообщение обратной связи</b>

📋 <b>Тип:</b> {feedback_data.get('type', 'Другое').title()}
📝 <b>Описание:</b> {feedback_data.get('description', 'Не указано')}
💡 <b>Предложение:</b> {feedback_data.get('suggestion', 'Не указано')}

👤 <b>Пользователь:</b>
• Имя: {user_info.get('name', 'Не авторизован')}
• Email: {user_info.get('email', 'Не указан')}
• Статус: {'Авторизован' if user_info.get('is_authenticated') else 'Не авторизован'}

🌐 <b>Страница:</b>
• URL: {page_info.get('url', 'Не указан')}
• Заголовок: {page_info.get('title', 'Не указан')}
• Браузер: {page_info.get('user_agent', 'Не указан')}
• Размер экрана: {page_info.get('screen_size', 'Не указан')}

⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        return message.strip()
    
    async def send_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправляет обратную связь в Telegram"""
        message = self.format_feedback_message(feedback_data)
        return await self.send_message(message)

# Глобальный экземпляр сервиса
telegram_service = TelegramService() 