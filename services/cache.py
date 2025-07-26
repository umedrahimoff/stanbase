import hashlib
import json
import time
from typing import Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta
import pickle
import os

class CacheManager:
    """Менеджер кеширования для оптимизации производительности"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 300):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl  # 5 минут по умолчанию
        
        # Создаем директорию для кеша если её нет
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерирует ключ кеша на основе аргументов"""
        # Создаем строку из аргументов
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        
        # Создаем хеш для короткого ключа
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"{prefix}_{key_hash}"
    
    def _get_cache_path(self, key: str) -> str:
        """Получает путь к файлу кеша"""
        return os.path.join(self.cache_dir, f"{key}.cache")
    
    def get(self, key: str) -> Optional[Any]:
        """Получает данные из кеша"""
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            # Проверяем TTL
            if time.time() > cached_data['expires_at']:
                # Удаляем устаревший кеш
                os.remove(cache_path)
                return None
            
            return cached_data['data']
        
        except (pickle.PickleError, KeyError, EOFError):
            # Удаляем поврежденный кеш
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Сохраняет данные в кеш"""
        if ttl is None:
            ttl = self.default_ttl
        
        cache_data = {
            'data': data,
            'created_at': time.time(),
            'expires_at': time.time() + ttl
        }
        
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Удаляет данные из кеша"""
        cache_path = self._get_cache_path(key)
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                return True
            except Exception:
                return False
        return False
    
    def clear(self, prefix: Optional[str] = None) -> int:
        """Очищает кеш"""
        deleted_count = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                if prefix is None or filename.startswith(prefix):
                    try:
                        os.remove(os.path.join(self.cache_dir, filename))
                        deleted_count += 1
                    except Exception:
                        continue
        
        return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику кеша"""
        total_files = 0
        total_size = 0
        expired_files = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                file_path = os.path.join(self.cache_dir, filename)
                total_files += 1
                total_size += os.path.getsize(file_path)
                
                # Проверяем, не истек ли срок действия
                try:
                    with open(file_path, 'rb') as f:
                        cached_data = pickle.load(f)
                    if time.time() > cached_data['expires_at']:
                        expired_files += 1
                except:
                    expired_files += 1
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'expired_files': expired_files,
            'cache_dir': self.cache_dir
        }

# Глобальный экземпляр кеш-менеджера
cache_manager = CacheManager()

def cached(prefix: str, ttl: Optional[int] = None):
    """Декоратор для кеширования результатов функций"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем ключ кеша
            cache_key = cache_manager._get_cache_key(prefix, *args, **kwargs)
            
            # Пытаемся получить из кеша
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию и кешируем результат
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

class QueryCache:
    """Кеширование для SQL запросов"""
    
    @staticmethod
    @cached("query", ttl=600)  # 10 минут для запросов
    def get_companies_with_filters(country: str = "", stage: str = "", industry: str = "", limit: int = 20, offset: int = 0):
        """Кешированный запрос компаний с фильтрами"""
        from db import SessionLocal
        from models import Company
        from sqlalchemy import and_
        
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
                'companies': companies,
                'total': total,
                'limit': limit,
                'offset': offset
            }
        finally:
            db.close()
    
    @staticmethod
    @cached("query", ttl=600)
    def get_investors_with_filters(country: str = "", focus: str = "", limit: int = 20, offset: int = 0):
        """Кешированный запрос инвесторов с фильтрами"""
        from db import SessionLocal
        from models import Investor
        
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
                'investors': investors,
                'total': total,
                'limit': limit,
                'offset': offset
            }
        finally:
            db.close()
    
    @staticmethod
    @cached("query", ttl=300)  # 5 минут для новостей
    def get_latest_news(limit: int = 10):
        """Кешированный запрос последних новостей"""
        from db import SessionLocal
        from models import News
        
        db = SessionLocal()
        try:
            news = db.query(News).filter(News.status == 'active').order_by(News.created_at.desc()).limit(limit).all()
            return news
        finally:
            db.close()
    
    @staticmethod
    @cached("query", ttl=1800)  # 30 минут для статистики
    def get_analytics_stats(year: Optional[int] = None):
        """Кешированная статистика"""
        from db import SessionLocal
        from models import Company, Investor, News, Job
        from sqlalchemy import func
        from datetime import datetime
        
        db = SessionLocal()
        try:
            # Базовые запросы
            total_companies = db.query(Company).filter(Company.status == 'active').count()
            total_investors = db.query(Investor).filter(Investor.status == 'active').count()
            total_news = db.query(News).filter(News.status == 'active').count()
            total_jobs = db.query(Job).filter(Job.status == 'active').count()
            
            # Статистика по странам
            companies_by_country = db.query(
                Company.country, 
                func.count(Company.id)
            ).filter(Company.status == 'active').group_by(Company.country).all()
            
            # Статистика по стадиям
            companies_by_stage = db.query(
                Company.stage, 
                func.count(Company.id)
            ).filter(Company.status == 'active').group_by(Company.stage).all()
            
            return {
                'total_companies': total_companies,
                'total_investors': total_investors,
                'total_news': total_news,
                'total_jobs': total_jobs,
                'companies_by_country': dict(companies_by_country),
                'companies_by_stage': dict(companies_by_stage)
            }
        finally:
            db.close()

class CacheInvalidator:
    """Инвалидатор кеша при изменениях данных"""
    
    @staticmethod
    def invalidate_companies():
        """Инвалидирует кеш компаний"""
        cache_manager.clear("query_companies")
        cache_manager.clear("query_analytics")
    
    @staticmethod
    def invalidate_investors():
        """Инвалидирует кеш инвесторов"""
        cache_manager.clear("query_investors")
        cache_manager.clear("query_analytics")
    
    @staticmethod
    def invalidate_news():
        """Инвалидирует кеш новостей"""
        cache_manager.clear("query_news")
    
    @staticmethod
    def invalidate_all():
        """Инвалидирует весь кеш"""
        cache_manager.clear() 