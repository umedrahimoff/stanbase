from db import SessionLocal
from models import Notification, User
from datetime import datetime
from typing import Optional, List

class NotificationService:
    """Сервис для работы с уведомлениями"""
    
    @staticmethod
    def create_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = 'info',
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None
    ) -> Notification:
        """Создает новое уведомление"""
        db = SessionLocal()
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                entity_type=entity_type,
                entity_id=entity_id
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification
        finally:
            db.close()
    
    @staticmethod
    def get_user_notifications(user_id: int, limit: int = 20, unread_only: bool = False) -> List[Notification]:
        """Получает уведомления пользователя"""
        db = SessionLocal()
        try:
            query = db.query(Notification).filter(Notification.user_id == user_id)
            if unread_only:
                query = query.filter(Notification.is_read == False)
            return query.order_by(Notification.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Отмечает уведомление как прочитанное"""
        db = SessionLocal()
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            if notification:
                notification.is_read = True
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Отмечает все уведомления пользователя как прочитанные"""
        db = SessionLocal()
        try:
            count = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).update({"is_read": True})
            db.commit()
            return count
        finally:
            db.close()
    
    @staticmethod
    def delete_notification(notification_id: int, user_id: int) -> bool:
        """Удаляет уведомление"""
        db = SessionLocal()
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            if notification:
                db.delete(notification)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Получает количество непрочитанных уведомлений"""
        db = SessionLocal()
        try:
            return db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).count()
        finally:
            db.close()

# Предустановленные типы уведомлений
class NotificationTypes:
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'

# Шаблоны уведомлений
class NotificationTemplates:
    @staticmethod
    def new_comment(entity_type: str, entity_name: str) -> dict:
        return {
            'title': 'Новый комментарий',
            'message': f'Добавлен новый комментарий к {entity_type}: {entity_name}',
            'type': NotificationTypes.INFO
        }
    
    @staticmethod
    def company_updated(company_name: str) -> dict:
        return {
            'title': 'Обновление компании',
            'message': f'Компания {company_name} была обновлена',
            'type': NotificationTypes.INFO
        }
    
    @staticmethod
    def new_job(company_name: str, job_title: str) -> dict:
        return {
            'title': 'Новая вакансия',
            'message': f'Компания {company_name} опубликовала новую вакансию: {job_title}',
            'type': NotificationTypes.SUCCESS
        }
    
    @staticmethod
    def investment_round(company_name: str, amount: str) -> dict:
        return {
            'title': 'Новый раунд инвестиций',
            'message': f'Компания {company_name} привлекла инвестиции на сумму {amount}',
            'type': NotificationTypes.SUCCESS
        } 