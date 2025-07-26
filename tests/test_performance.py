#!/usr/bin/env python3
"""
Тест оптимизации производительности: кеширование и пагинация
"""

import time
import requests
from services.cache import cache_manager, QueryCache, CacheInvalidator
from services.pagination import PaginationHelper, DatabasePagination
from db import SessionLocal
from models import Company, Investor, News

def test_cache_performance():
    """Тестируем производительность кеширования"""
    print("🚀 Тестируем производительность кеширования...")
    
    # Очищаем кеш перед тестом
    cache_manager.clear()
    
    # Тест 1: Первый запрос (без кеша)
    print("\n📊 Тест 1: Первый запрос (без кеша)")
    start_time = time.time()
    
    result1 = QueryCache.get_companies_with_filters(
        country="KZ",
        stage="seed",
        limit=20,
        offset=0
    )
    
    first_query_time = time.time() - start_time
    print(f"⏱️  Время первого запроса: {first_query_time:.4f} сек")
    print(f"📋 Получено компаний: {len(result1['companies'])}")
    
    # Тест 2: Повторный запрос (с кешем)
    print("\n📊 Тест 2: Повторный запрос (с кешем)")
    start_time = time.time()
    
    result2 = QueryCache.get_companies_with_filters(
        country="KZ",
        stage="seed",
        limit=20,
        offset=0
    )
    
    cached_query_time = time.time() - start_time
    print(f"⏱️  Время кешированного запроса: {cached_query_time:.4f} сек")
    print(f"📋 Получено компаний: {len(result2['companies'])}")
    
    # Вычисляем ускорение
    if first_query_time > 0:
        speedup = first_query_time / cached_query_time
        print(f"⚡ Ускорение: {speedup:.2f}x")
    
    # Проверяем, что результаты одинаковые
    assert len(result1['companies']) == len(result2['companies'])
    print("✅ Результаты кеширования корректны")

def test_pagination_performance():
    """Тестируем производительность пагинации"""
    print("\n🚀 Тестируем производительность пагинации...")
    
    db = SessionLocal()
    try:
        # Получаем общее количество записей
        total_companies = db.query(Company).filter(Company.status == 'active').count()
        print(f"📊 Всего компаний в базе: {total_companies}")
        
        # Тест пагинации с разными размерами страниц
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            print(f"\n📄 Тест пагинации с размером страницы: {page_size}")
            
            start_time = time.time()
            
            # Используем DatabasePagination
            result = DatabasePagination.get_paginated_results(
                db.query(Company).filter(Company.status == 'active'),
                page=1,
                per_page=page_size
            )
            
            query_time = time.time() - start_time
            print(f"⏱️  Время запроса: {query_time:.4f} сек")
            print(f"📋 Получено записей: {len(result['items'])}")
            print(f"📄 Всего страниц: {result['pages']}")
            
            # Проверяем корректность пагинации
            assert len(result['items']) <= page_size
            assert result['total'] == total_companies
            
    finally:
        db.close()
    
    print("✅ Пагинация работает корректно")

def test_cache_invalidation():
    """Тестируем инвалидацию кеша"""
    print("\n🚀 Тестируем инвалидацию кеша...")
    
    # Создаем тестовые данные в кеше
    cache_manager.set("test_key", "test_value", ttl=3600)
    
    # Проверяем, что данные есть в кеше
    cached_value = cache_manager.get("test_key")
    assert cached_value == "test_value"
    print("✅ Данные успешно сохранены в кеш")
    
    # Тестируем инвалидацию
    CacheInvalidator.invalidate_companies()
    print("✅ Инвалидация кеша компаний выполнена")
    
    CacheInvalidator.invalidate_all()
    print("✅ Полная инвалидация кеша выполнена")
    
    # Проверяем, что тестовые данные удалены
    cached_value_after = cache_manager.get("test_key")
    assert cached_value_after is None
    print("✅ Кеш успешно очищен")

def test_pagination_helper():
    """Тестируем хелпер пагинации"""
    print("\n🚀 Тестируем хелпер пагинации...")
    
    # Тест параметров пагинации
    params = PaginationHelper.get_pagination_params(page=5, per_page=25)
    print(f"📄 Параметры пагинации: {params}")
    
    assert params['page'] == 5
    assert params['per_page'] == 25
    assert params['offset'] == 100
    
    # Тест создания объекта пагинации
    test_items = [f"item_{i}" for i in range(50)]
    pagination = PaginationHelper.create_pagination(
        items=test_items,
        total=100,
        page=2,
        per_page=20,
        request_url="/test",
        query_params={'filter': 'test'}
    )
    
    print(f"📊 Информация о пагинации: {pagination.get_pagination_info()}")
    print(f"🔗 Ссылки пагинации: {len(pagination.get_pagination_links())} ссылок")
    
    assert pagination.has_prev
    assert pagination.has_next
    assert pagination.pages == 5
    
    print("✅ Хелпер пагинации работает корректно")

def test_cache_stats():
    """Тестируем статистику кеша"""
    print("\n🚀 Тестируем статистику кеша...")
    
    # Создаем тестовые данные
    for i in range(5):
        cache_manager.set(f"test_key_{i}", f"test_value_{i}", ttl=3600)
    
    # Получаем статистику
    stats = cache_manager.get_stats()
    print(f"📊 Статистика кеша: {stats}")
    
    assert stats['total_files'] >= 5
    assert stats['total_size_mb'] >= 0
    
    print("✅ Статистика кеша работает корректно")

def test_api_endpoints():
    """Тестируем API эндпоинты (если сервер запущен)"""
    print("\n🚀 Тестируем API эндпоинты...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Тест получения компаний через API
        response = requests.get(f"{base_url}/api/v1/companies?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API компаний работает: получено {len(data.get('companies', []))} компаний")
        else:
            print(f"❌ API компаний вернул статус: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Сервер не запущен или недоступен: {e}")
    
    try:
        # Тест получения инвесторов через API
        response = requests.get(f"{base_url}/api/v1/investors?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API инвесторов работает: получено {len(data.get('investors', []))} инвесторов")
        else:
            print(f"❌ API инвесторов вернул статус: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Сервер не запущен или недоступен: {e}")

def performance_benchmark():
    """Бенчмарк производительности"""
    print("\n🚀 Запускаем бенчмарк производительности...")
    
    db = SessionLocal()
    try:
        # Бенчмарк 1: Запрос без кеша
        print("\n📊 Бенчмарк 1: Запрос без кеша")
        start_time = time.time()
        
        companies = db.query(Company).filter(Company.status == 'active').limit(100).all()
        
        no_cache_time = time.time() - start_time
        print(f"⏱️  Время запроса без кеша: {no_cache_time:.4f} сек")
        print(f"📋 Получено записей: {len(companies)}")
        
        # Бенчмарк 2: Запрос с кешем
        print("\n📊 Бенчмарк 2: Запрос с кешем")
        start_time = time.time()
        
        cached_result = QueryCache.get_companies_with_filters(limit=100, offset=0)
        
        cache_time = time.time() - start_time
        print(f"⏱️  Время запроса с кешем: {cache_time:.4f} сек")
        print(f"📋 Получено записей: {len(cached_result['companies'])}")
        
        # Вычисляем улучшение производительности
        if no_cache_time > 0:
            improvement = ((no_cache_time - cache_time) / no_cache_time) * 100
            print(f"📈 Улучшение производительности: {improvement:.1f}%")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 Запускаем тесты оптимизации производительности...\n")
    
    try:
        test_cache_performance()
        test_pagination_performance()
        test_cache_invalidation()
        test_pagination_helper()
        test_cache_stats()
        test_api_endpoints()
        performance_benchmark()
        
        print("\n🎉 Все тесты оптимизации производительности завершены успешно!")
        print("\n📋 Резюме оптимизаций:")
        print("✅ Система кеширования с TTL и автоматической очисткой")
        print("✅ Улучшенная пагинация с навигацией и селектором")
        print("✅ API для управления кешем")
        print("✅ Инвалидация кеша при изменениях данных")
        print("✅ Статистика и мониторинг кеша")
        print("✅ Оптимизированные запросы к базе данных")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc() 