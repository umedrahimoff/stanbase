"""
Модуль для обработки и оптимизации изображений
"""
import os
from PIL import Image
from io import BytesIO
import uuid


class ImageProcessor:
    """Класс для обработки изображений"""
    
    @staticmethod
    def optimize_image(image_data: bytes, max_size: tuple = (800, 800), quality: int = 85) -> bytes:
        """
        Оптимизирует изображение: изменяет размер и сжимает
        
        Args:
            image_data: байты изображения
            max_size: максимальный размер (ширина, высота)
            quality: качество сжатия (1-100)
            
        Returns:
            bytes: оптимизированное изображение
        """
        try:
            # Открываем изображение
            image = Image.open(BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Изменяем размер если изображение слишком большое
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Сохраняем в байты с оптимизацией
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"Ошибка оптимизации изображения: {e}")
            return image_data
    
    @staticmethod
    def create_thumbnail(image_data: bytes, size: tuple = (150, 150)) -> bytes:
        """
        Создает thumbnail изображения
        
        Args:
            image_data: байты исходного изображения
            size: размер thumbnail (ширина, высота)
            
        Returns:
            bytes: thumbnail изображение
        """
        try:
            image = Image.open(BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Создаем thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Сохраняем в байты
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"Ошибка создания thumbnail: {e}")
            return image_data
    
    @staticmethod
    def generate_filename(original_filename: str, prefix: str = "") -> str:
        """
        Генерирует уникальное имя файла
        
        Args:
            original_filename: исходное имя файла
            prefix: префикс для имени
            
        Returns:
            str: уникальное имя файла
        """
        # Получаем расширение
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.jpg'
        
        # Генерируем уникальное имя
        unique_id = str(uuid.uuid4())
        return f"{prefix}_{unique_id}{ext}" if prefix else f"{unique_id}{ext}"
    
    @staticmethod
    def validate_image(image_data: bytes, max_size_mb: int = 5) -> bool:
        """
        Проверяет валидность изображения
        
        Args:
            image_data: байты изображения
            max_size_mb: максимальный размер в МБ
            
        Returns:
            bool: True если изображение валидно
        """
        try:
            # Проверяем размер файла
            if len(image_data) > max_size_mb * 1024 * 1024:
                return False
            
            # Проверяем что это действительно изображение
            image = Image.open(BytesIO(image_data))
            image.verify()
            return True
            
        except Exception:
            return False 