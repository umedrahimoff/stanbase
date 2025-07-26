import secrets
import hashlib
import time
from typing import Optional

class CSRFProtection:
    """Класс для защиты от CSRF атак"""
    
    def __init__(self, secret_key: str = "stanbase_csrf_secret_2024"):
        self.secret_key = secret_key
    
    def generate_token(self, user_id: int, session_id: str) -> str:
        """Генерирует CSRF токен для пользователя"""
        # Создаем уникальный токен на основе пользователя, сессии и времени
        data = f"{user_id}:{session_id}:{int(time.time())}"
        token = hashlib.sha256((data + self.secret_key).encode()).hexdigest()
        return token
    
    def verify_token(self, token: str, user_id: int, session_id: str, max_age: int = 3600) -> bool:
        """Проверяет CSRF токен"""
        if not token:
            return False
        
        # Проверяем токен для последних max_age секунд
        current_time = int(time.time())
        for i in range(max_age):
            check_time = current_time - i
            data = f"{user_id}:{session_id}:{check_time}"
            expected_token = hashlib.sha256((data + self.secret_key).encode()).hexdigest()
            if token == expected_token:
                return True
        
        return False

# Глобальный экземпляр CSRF защиты
csrf_protection = CSRFProtection()

def get_csrf_token(request) -> Optional[str]:
    """Получает CSRF токен для текущего пользователя"""
    user_id = request.session.get("user_id")
    session_id = request.session.get("session_id")
    
    if not user_id or not session_id:
        return None
    
    return csrf_protection.generate_token(user_id, session_id)

def verify_csrf_token(request, token: str) -> bool:
    """Проверяет CSRF токен"""
    user_id = request.session.get("user_id")
    session_id = request.session.get("session_id")
    
    if not user_id or not session_id:
        return False
    
    return csrf_protection.verify_token(token, user_id, session_id) 