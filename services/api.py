from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from db import SessionLocal
from models import User, Company, Investor, News, Job, Comment, Notification, Feedback
from utils.security import verify_token
from .notifications import NotificationService, NotificationTemplates
from .comments import CommentService, CommentValidator
from .cache import cache_manager, CacheInvalidator
from .telegram import telegram_service

# Создаем роутер для API
api_router = APIRouter(prefix="/api/v1", tags=["API"])

# Зависимость для получения текущего пользователя
def get_current_user(token: str = Query(..., alias="token")):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return payload

# Зависимость для получения базы данных
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === API для уведомлений ===

@api_router.get("/notifications")
async def get_notifications(
    token: str = Query(..., alias="token"),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False)
):
    """Получить уведомления пользователя"""
    user_data = get_current_user(token)
    user_id = user_data.get("user_id")
    
    notifications = NotificationService.get_user_notifications(
        user_id=user_id,
        limit=limit,
        unread_only=unread_only
    )
    
    return {
        "success": True,
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "entity_type": n.entity_type,
                "entity_id": n.entity_id,
                "created_at": n.created_at.isoformat()
            }
            for n in notifications
        ]
    }

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int = Path(...),
    token: str = Query(..., alias="token")
):
    """Отметить уведомление как прочитанное"""
    user_data = get_current_user(token)
    user_id = user_data.get("user_id")
    
    success = NotificationService.mark_as_read(notification_id, user_id)
    
    return {
        "success": success,
        "message": "Уведомление отмечено как прочитанное" if success else "Уведомление не найдено"
    }

@api_router.post("/notifications/read-all")
async def mark_all_notifications_read(token: str = Query(..., alias="token")):
    """Отметить все уведомления как прочитанные"""
    user_data = get_current_user(token)
    user_id = user_data.get("user_id")
    
    count = NotificationService.mark_all_as_read(user_id)
    
    return {
        "success": True,
        "message": f"Отмечено {count} уведомлений как прочитанные",
        "count": count
    }

@api_router.get("/notifications/unread-count")
async def get_unread_count(token: str = Query(..., alias="token")):
    """Получить количество непрочитанных уведомлений"""
    user_data = get_current_user(token)
    user_id = user_data.get("user_id")
    
    count = NotificationService.get_unread_count(user_id)
    
    return {
        "success": True,
        "count": count
    }

# === API для комментариев ===

@api_router.get("/comments/{entity_type}/{entity_id}")
async def get_comments(
    entity_type: str = Path(...),
    entity_id: int = Path(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Получить комментарии для сущности"""
    if not CommentValidator.is_valid_entity_type(entity_type):
        raise HTTPException(status_code=400, detail="Неверный тип сущности")
    
    comments = CommentService.get_comments(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset
    )
    
    # Получаем ответы для каждого комментария
    result = []
    for comment in comments:
        replies = CommentService.get_replies(comment.id)
        result.append({
            "id": comment.id,
            "content": comment.content,
            "user": {
                "id": comment.user.id,
                "name": f"{comment.user.first_name} {comment.user.last_name}",
                "email": comment.user.email
            },
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
            "replies": [
                {
                    "id": reply.id,
                    "content": reply.content,
                    "user": {
                        "id": reply.user.id,
                        "name": f"{reply.user.first_name} {reply.user.last_name}",
                        "email": reply.user.email
                    },
                    "created_at": reply.created_at.isoformat()
                }
                for reply in replies
            ]
        })
    
    return {
        "success": True,
        "comments": result,
        "total": CommentService.get_comment_count(entity_type, entity_id)
    }

@api_router.post("/comments")
async def create_comment(
    entity_type: str = Query(...),
    entity_id: int = Query(...),
    content: str = Query(...),
    parent_id: Optional[int] = Query(None),
    token: str = Query(..., alias="token")
):
    """Создать новый комментарий"""
    user_data = get_current_user(token)
    user_id = user_data.get("user_id")
    
    # Валидация
    if not CommentValidator.is_valid_entity_type(entity_type):
        raise HTTPException(status_code=400, detail="Неверный тип сущности")
    
    validation_errors = CommentValidator.validate_content(content)
    if validation_errors:
        raise HTTPException(status_code=400, detail=f"Ошибки валидации: {validation_errors}")
    
    # Создание комментария
    comment = CommentService.create_comment(
        user_id=user_id,
        content=content,
        entity_type=entity_type,
        entity_id=entity_id,
        parent_id=parent_id
    )
    
    return {
        "success": True,
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat()
        },
        "message": "Комментарий успешно добавлен"
    }

@api_router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: int = Path(...),
    content: str = Query(...),
    token: str = Query(..., alias="token")
):
    """Обновить комментарий"""
    user_data = get_current_user(token)
    user_id = user_data.get("user_id")
    
    # Валидация
    validation_errors = CommentValidator.validate_content(content)
    if validation_errors:
        raise HTTPException(status_code=400, detail=f"Ошибки валидации: {validation_errors}")
    
    # Обновление комментария
    success = CommentService.update_comment(comment_id, user_id, content)
    
    return {
        "success": success,
        "message": "Комментарий обновлен" if success else "Комментарий не найден или нет прав"
    }

@api_router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int = Path(...),
    token: str = Query(..., alias="token")
):
    """Удалить комментарий"""
    user_data = get_current_user(token)
    user_id = user_data.get("user_id")
    is_admin = user_data.get("role") in ["admin", "moderator"]
    
    success = CommentService.delete_comment(comment_id, user_id, is_admin)
    
    return {
        "success": success,
        "message": "Комментарий удален" if success else "Комментарий не найден или нет прав"
    }

# === API для компаний ===

@api_router.get("/companies")
async def get_companies_api(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    country: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    industry: Optional[str] = Query(None)
):
    """Получить список компаний"""
    db = SessionLocal()
    try:
        query = db.query(Company).filter(Company.status == 'active')
        
        if country:
            query = query.filter(Company.country == country)
        if stage:
            query = query.filter(Company.stage == stage)
        if industry:
            query = query.filter(Company.industry == industry)
        
        total = query.count()
        companies = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "companies": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "country": c.country,
                    "city": c.city,
                    "stage": c.stage,
                    "industry": c.industry,
                    "website": c.website,
                    "founded_date": c.founded_date.isoformat() if c.founded_date else None
                }
                for c in companies
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close()

@api_router.get("/companies/{company_id}")
async def get_company_api(company_id: int = Path(...)):
    """Получить детальную информацию о компании"""
    db = SessionLocal()
    try:
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.status == 'active'
        ).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Компания не найдена")
        
        return {
            "success": True,
            "company": {
                "id": company.id,
                "name": company.name,
                "description": company.description,
                "country": company.country,
                "city": company.city,
                "stage": company.stage,
                "industry": company.industry,
                "website": company.website,
                "founded_date": company.founded_date.isoformat() if company.founded_date else None,
                "created_at": company.created_at.isoformat()
            }
        }
    finally:
        db.close()

# === API для инвесторов ===

@api_router.get("/investors")
async def get_investors_api(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    country: Optional[str] = Query(None),
    focus: Optional[str] = Query(None)
):
    """Получить список инвесторов"""
    db = SessionLocal()
    try:
        query = db.query(Investor).filter(Investor.status == 'active')
        
        if country:
            query = query.filter(Investor.country == country)
        if focus:
            query = query.filter(Investor.focus.contains(focus))
        
        total = query.count()
        investors = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "investors": [
                {
                    "id": i.id,
                    "name": i.name,
                    "description": i.description,
                    "country": i.country,
                    "focus": i.focus,
                    "stages": i.stages,
                    "website": i.website,
                    "type": i.type
                }
                for i in investors
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close()

# === API для вакансий ===

@api_router.get("/jobs")
async def get_jobs_api(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    city: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None)
):
    """Получить список вакансий"""
    db = SessionLocal()
    try:
        query = db.query(Job).filter(Job.status == 'active')
        
        if city:
            query = query.filter(Job.city == city)
        if job_type:
            query = query.filter(Job.job_type == job_type)
        
        total = query.count()
        jobs = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "description": j.description,
                    "city": j.city,
                    "job_type": j.job_type,
                    "contact": j.contact,
                    "company": {
                        "id": j.company.id,
                        "name": j.company.name
                    } if j.company else None
                }
                for j in jobs
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close() 

# === API для обратной связи ===

@api_router.post("/feedback")
async def submit_feedback(
    type: str = Query(..., description="Тип обратной связи"),
    description: str = Query(..., description="Описание проблемы"),
    suggestion: str = Query("", description="Предложение пользователя"),
    page_url: str = Query(..., description="URL страницы"),
    page_title: str = Query("", description="Заголовок страницы"),
    user_agent: str = Query("", description="User Agent браузера"),
    screen_size: str = Query("", description="Размер экрана"),
    user_name: str = Query("", description="Имя пользователя"),
    user_email: str = Query("", description="Email пользователя"),
    is_authenticated: bool = Query(False, description="Авторизован ли пользователь")
):
    """Отправить обратную связь в Telegram и сохранить в базе данных"""
    
    feedback_data = {
        "type": type,
        "description": description,
        "suggestion": suggestion,
        "user_info": {
            "name": user_name,
            "email": user_email,
            "is_authenticated": is_authenticated
        },
        "page_info": {
            "url": page_url,
            "title": page_title,
            "user_agent": user_agent,
            "screen_size": screen_size
        }
    }
    
    # Сохраняем в базе данных
    db = SessionLocal()
    try:
        feedback = Feedback(
            type=type,
            description=description,
            suggestion=suggestion if suggestion else None,
            name=user_name if user_name else None,
            email=user_email if user_email else None,
            page_url=page_url,
            page_title=page_title,
            user_agent=user_agent,
            screen_size=screen_size,
            is_authenticated=is_authenticated,
            status='new'
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": "Ошибка при сохранении обратной связи",
            "error": str(e)
        }
    finally:
        db.close()
    
    # Отправляем в Telegram
    result = await telegram_service.send_feedback(feedback_data)
    
    if result["success"]:
        return {
            "success": True,
            "message": "Обратная связь отправлена успешно"
        }
    else:
        return {
            "success": False,
            "message": "Обратная связь сохранена, но ошибка при отправке в Telegram",
            "error": result.get("error", "Неизвестная ошибка")
        }

# === API для управления кешем ===

@api_router.get("/cache/stats")
async def get_cache_stats(token: str = Query(..., alias="token")):
    """Получить статистику кеша (только для админов)"""
    user_data = get_current_user(token)
    user_role = user_data.get("role")
    
    if user_role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    stats = cache_manager.get_stats()
    
    return {
        "success": True,
        "stats": stats
    }

@api_router.post("/cache/clear")
async def clear_cache(
    prefix: Optional[str] = Query(None, description="Префикс для очистки конкретного типа кеша"),
    token: str = Query(..., alias="token")
):
    """Очистить кеш (только для админов)"""
    user_data = get_current_user(token)
    user_role = user_data.get("role")
    
    if user_role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    deleted_count = cache_manager.clear(prefix)
    
    return {
        "success": True,
        "message": f"Удалено {deleted_count} файлов кеша",
        "deleted_count": deleted_count
    }

@api_router.post("/cache/invalidate/companies")
async def invalidate_companies_cache(token: str = Query(..., alias="token")):
    """Инвалидировать кеш компаний (только для админов)"""
    user_data = get_current_user(token)
    user_role = user_data.get("role")
    
    if user_role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    CacheInvalidator.invalidate_companies()
    
    return {
        "success": True,
        "message": "Кеш компаний инвалидирован"
    }

@api_router.post("/cache/invalidate/investors")
async def invalidate_investors_cache(token: str = Query(..., alias="token")):
    """Инвалидировать кеш инвесторов (только для админов)"""
    user_data = get_current_user(token)
    user_role = user_data.get("role")
    
    if user_role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    CacheInvalidator.invalidate_investors()
    
    return {
        "success": True,
        "message": "Кеш инвесторов инвалидирован"
    }

@api_router.post("/cache/invalidate/news")
async def invalidate_news_cache(token: str = Query(..., alias="token")):
    """Инвалидировать кеш новостей (только для админов)"""
    user_data = get_current_user(token)
    user_role = user_data.get("role")
    
    if user_role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    CacheInvalidator.invalidate_news()
    
    return {
        "success": True,
        "message": "Кеш новостей инвалидирован"
    }

@api_router.post("/cache/invalidate/all")
async def invalidate_all_cache(token: str = Query(..., alias="token")):
    """Инвалидировать весь кеш (только для админов)"""
    user_data = get_current_user(token)
    user_role = user_data.get("role")
    
    if user_role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    CacheInvalidator.invalidate_all()
    
    return {
        "success": True,
        "message": "Весь кеш инвалидирован"
    } 