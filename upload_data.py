import requests
import os
import json

def upload_data_to_production():
    """Загрузка данных на продакшн сервер"""
    
    # Найти последний файл экспорта
    export_files = [f for f in os.listdir('.') if f.startswith('export_data_') and f.endswith('.json')]
    if not export_files:
        print("Файл экспорта не найден. Сначала запустите export_data.py")
        return
    
    latest_file = max(export_files)
    print(f"Загружаем файл: {latest_file}")
    
    # URL продакшн сервера
    PRODUCTION_URL = "https://stanbasetech.onrender.com"
    
    try:
        # Сначала запускаем миграцию
        print("Запускаем миграцию...")
        migration_response = requests.get(f"{PRODUCTION_URL}/run-migration")
        migration_result = migration_response.json()
        
        if not migration_result.get('success'):
            print(f"Ошибка миграции: {migration_result.get('error')}")
            return
        
        print("Миграция выполнена успешно")
        
        # Теперь импортируем данные
        print("Импортируем данные...")
        
        # Загружаем данные из файла
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        import_response = requests.post(f"{PRODUCTION_URL}/import-data", json=data)
        import_result = import_response.json()
        
        if not import_result.get('success'):
            print(f"Ошибка импорта: {import_result.get('error')}")
            return
        
        print("Импорт выполнен успешно!")
        print(f"Результат: {import_result.get('message')}")
        
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")

if __name__ == "__main__":
    upload_data_to_production() 