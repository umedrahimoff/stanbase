from db import SessionLocal
from models import Comment, User
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import and_

class CommentService:
    """Сервис для работы с комментариями"""
    
    @staticmethod
    def create_comment(
        user_id: int,
        content: str,
        entity_type: str,
        entity_id: int,
        parent_id: Optional[int] = None
    ) -> Comment:
        """Создает новый комментарий"""
        db = SessionLocal()
        try:
            comment = Comment(
                user_id=user_id,
                content=content,
                entity_type=entity_type,
                entity_id=entity_id,
                parent_id=parent_id
            )
            db.add(comment)
            db.commit()
            db.refresh(comment)
            return comment
        finally:
            db.close()
    
    @staticmethod
    def get_comments(
        entity_type: str,
        entity_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Comment]:
        """Получает комментарии для сущности"""
        db = SessionLocal()
        try:
            return db.query(Comment).filter(
                and_(
                    Comment.entity_type == entity_type,
                    Comment.entity_id == entity_id,
                    Comment.status == 'active',
                    Comment.parent_id.is_(None)  # только корневые комментарии
                )
            ).order_by(Comment.created_at.desc()).offset(offset).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def get_replies(comment_id: int) -> List[Comment]:
        """Получает ответы на комментарий"""
        db = SessionLocal()
        try:
            return db.query(Comment).filter(
                and_(
                    Comment.parent_id == comment_id,
                    Comment.status == 'active'
                )
            ).order_by(Comment.created_at.asc()).all()
        finally:
            db.close()
    
    @staticmethod
    def update_comment(comment_id: int, user_id: int, content: str) -> bool:
        """Обновляет комментарий"""
        db = SessionLocal()
        try:
            comment = db.query(Comment).filter(
                and_(
                    Comment.id == comment_id,
                    Comment.user_id == user_id,
                    Comment.status == 'active'
                )
            ).first()
            if comment:
                comment.content = content
                comment.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def delete_comment(comment_id: int, user_id: int, is_admin: bool = False) -> bool:
        """Удаляет комментарий (мягкое удаление)"""
        db = SessionLocal()
        try:
            query = db.query(Comment).filter(Comment.id == comment_id)
            if not is_admin:
                query = query.filter(Comment.user_id == user_id)
            
            comment = query.first()
            if comment:
                comment.status = 'deleted'
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_comment_count(entity_type: str, entity_id: int) -> int:
        """Получает количество комментариев для сущности"""
        db = SessionLocal()
        try:
            return db.query(Comment).filter(
                and_(
                    Comment.entity_type == entity_type,
                    Comment.entity_id == entity_id,
                    Comment.status == 'active'
                )
            ).count()
        finally:
            db.close()
    
    @staticmethod
    def get_user_comments(user_id: int, limit: int = 20) -> List[Comment]:
        """Получает комментарии пользователя"""
        db = SessionLocal()
        try:
            return db.query(Comment).filter(
                and_(
                    Comment.user_id == user_id,
                    Comment.status == 'active'
                )
            ).order_by(Comment.created_at.desc()).limit(limit).all()
        finally:
            db.close()

# Валидация комментариев
class CommentValidator:
    @staticmethod
    def validate_content(content: str) -> Dict[str, bool]:
        """Валидирует содержимое комментария"""
        errors = {}
        
        if not content or not content.strip():
            errors['empty'] = True
        
        if len(content.strip()) < 3:
            errors['too_short'] = True
        
        if len(content.strip()) > 2000:
            errors['too_long'] = True
        
        # Проверка на спам (простая проверка)
        spam_words = ['spam', 'реклама', 'купить', 'продать', 'http://', 'https://']
        content_lower = content.lower()
        if any(word in content_lower for word in spam_words):
            errors['spam'] = True
        
        return errors
    
    @staticmethod
    def is_valid_entity_type(entity_type: str) -> bool:
        """Проверяет, является ли тип сущности допустимым"""
        valid_types = ['company', 'investor', 'news', 'job', 'event']
        return entity_type in valid_types 