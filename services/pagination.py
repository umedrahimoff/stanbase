from typing import List, Dict, Any, Optional
from math import ceil
from urllib.parse import urlencode

class Pagination:
    """Класс для работы с пагинацией"""
    
    def __init__(
        self,
        items: List[Any],
        page: int = 1,
        per_page: int = 20,
        total: Optional[int] = None,
        base_url: str = "",
        query_params: Optional[Dict[str, Any]] = None
    ):
        self.items = items
        self.page = max(1, page)
        self.per_page = max(1, per_page)
        self.total = total or len(items)
        self.base_url = base_url
        self.query_params = query_params or {}
        
        # Вычисляем общее количество страниц
        self.pages = ceil(self.total / self.per_page) if self.total > 0 else 1
        
        # Проверяем валидность текущей страницы
        if self.page > self.pages:
            self.page = self.pages
    
    @property
    def has_prev(self) -> bool:
        """Есть ли предыдущая страница"""
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """Есть ли следующая страница"""
        return self.page < self.pages
    
    @property
    def prev_page(self) -> Optional[int]:
        """Номер предыдущей страницы"""
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_page(self) -> Optional[int]:
        """Номер следующей страницы"""
        return self.page + 1 if self.has_next else None
    
    @property
    def start_index(self) -> int:
        """Индекс первого элемента на текущей странице"""
        return (self.page - 1) * self.per_page
    
    @property
    def end_index(self) -> int:
        """Индекс последнего элемента на текущей странице"""
        return min(self.start_index + self.per_page, self.total)
    
    def get_page_url(self, page: int) -> str:
        """Генерирует URL для указанной страницы"""
        if not self.base_url:
            return ""
        
        params = self.query_params.copy()
        params['page'] = page
        
        # Убираем параметр page если это первая страница
        if page == 1:
            params.pop('page', None)
        
        query_string = urlencode(params) if params else ""
        separator = "&" if "?" in self.base_url else "?"
        
        return f"{self.base_url}{separator}{query_string}" if query_string else self.base_url
    
    def get_pagination_info(self) -> Dict[str, Any]:
        """Возвращает информацию о пагинации"""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'start_index': self.start_index,
            'end_index': self.end_index,
            'items_count': len(self.items)
        }
    
    def get_pagination_links(self, max_visible: int = 5) -> List[Dict[str, Any]]:
        """Генерирует ссылки для пагинации с ограниченным количеством видимых страниц"""
        links = []
        
        if self.pages <= 1:
            return links
        
        # Определяем диапазон видимых страниц
        start_page = max(1, self.page - max_visible // 2)
        end_page = min(self.pages, start_page + max_visible - 1)
        
        # Корректируем начало если конец слишком близко к концу
        if end_page - start_page < max_visible - 1:
            start_page = max(1, end_page - max_visible + 1)
        
        # Добавляем ссылку на первую страницу
        if start_page > 1:
            links.append({
                'page': 1,
                'url': self.get_page_url(1),
                'is_current': False,
                'is_ellipsis': False
            })
            
            if start_page > 2:
                links.append({
                    'page': None,
                    'url': '',
                    'is_current': False,
                    'is_ellipsis': True
                })
        
        # Добавляем видимые страницы
        for page in range(start_page, end_page + 1):
            links.append({
                'page': page,
                'url': self.get_page_url(page),
                'is_current': page == self.page,
                'is_ellipsis': False
            })
        
        # Добавляем ссылку на последнюю страницу
        if end_page < self.pages:
            if end_page < self.pages - 1:
                links.append({
                    'page': None,
                    'url': '',
                    'is_current': False,
                    'is_ellipsis': True
                })
            
            links.append({
                'page': self.pages,
                'url': self.get_page_url(self.pages),
                'is_current': False,
                'is_ellipsis': False
            })
        
        return links

class PaginationHelper:
    """Хелпер для работы с пагинацией в FastAPI"""
    
    @staticmethod
    def get_pagination_params(
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
    ) -> Dict[str, int]:
        """Получает параметры пагинации с валидацией"""
        page = max(1, page)
        per_page = max(1, min(per_page, max_per_page))
        
        return {
            'page': page,
            'per_page': per_page,
            'offset': (page - 1) * per_page
        }
    
    @staticmethod
    def create_pagination(
        items: List[Any],
        total: int,
        page: int,
        per_page: int,
        request_url: str,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Pagination:
        """Создает объект пагинации"""
        # Очищаем параметры от None значений
        if query_params:
            query_params = {k: v for k, v in query_params.items() if v is not None}
        
        return Pagination(
            items=items,
            page=page,
            per_page=per_page,
            total=total,
            base_url=request_url,
            query_params=query_params
        )

class DatabasePagination:
    """Пагинация для работы с базой данных"""
    
    @staticmethod
    def paginate_query(query, page: int = 1, per_page: int = 20):
        """Применяет пагинацию к SQLAlchemy запросу"""
        offset = (page - 1) * per_page
        
        # Получаем общее количество записей
        total = query.count()
        
        # Применяем пагинацию
        paginated_query = query.offset(offset).limit(per_page)
        
        return paginated_query, total
    
    @staticmethod
    def get_paginated_results(query, page: int = 1, per_page: int = 20):
        """Получает пагинированные результаты из запроса"""
        paginated_query, total = DatabasePagination.paginate_query(query, page, per_page)
        items = paginated_query.all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': ceil(total / per_page) if total > 0 else 1
        } 