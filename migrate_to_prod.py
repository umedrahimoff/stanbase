import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Данные для подключения к продакшн базе данных Render
DATABASE_URL = os.getenv('DATABASE_URL')

def migrate_production_database():
    """Миграция продакшн базы данных"""
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Подключение к продакшн базе данных установлено")
        
        # Проверяем, существует ли колонка logo в таблице investor
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'investor' AND column_name = 'logo'
        """)
        
        if not cursor.fetchone():
            print("Добавляем колонку logo в таблицу investor...")
            cursor.execute("ALTER TABLE investor ADD COLUMN logo VARCHAR(256)")
            print("Колонка logo успешно добавлена")
        else:
            print("Колонка logo уже существует")
        
        # Проверяем, существует ли таблица currency
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'currency'
        """)
        
        if not cursor.fetchone():
            print("Создаем таблицу currency...")
            cursor.execute("""
                CREATE TABLE currency (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(8) UNIQUE NOT NULL,
                    name VARCHAR(64) NOT NULL,
                    symbol VARCHAR(8),
                    status VARCHAR(16) DEFAULT 'active'
                )
            """)
            print("Таблица currency успешно создана")
            
            # Добавляем базовые валюты
            currencies = [
                ("USD", "Доллар США", "$", "active"),
                ("EUR", "Евро", "€", "active"),
                ("KZT", "Тенге", "₸", "active"),
                ("RUB", "Рубль", "₽", "active"),
                ("UZS", "Сум", "so'm", "active"),
                ("GBP", "Фунт стерлингов", "£", "active"),
                ("CNY", "Юань", "¥", "active"),
            ]
            
            cursor.executemany(
                "INSERT INTO currency (code, name, symbol, status) VALUES (%s, %s, %s, %s)",
                currencies
            )
            print("Базовые валюты добавлены")
        else:
            print("Таблица currency уже существует")
        
        # Проверяем, существует ли колонка currency_id в таблице deal
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'deal' AND column_name = 'currency_id'
        """)
        
        if not cursor.fetchone():
            print("Добавляем колонку currency_id в таблицу deal...")
            cursor.execute("ALTER TABLE deal ADD COLUMN currency_id INTEGER REFERENCES currency(id)")
            print("Колонка currency_id успешно добавлена")
            
            # Устанавливаем USD как валюту по умолчанию для существующих сделок
            cursor.execute("UPDATE deal SET currency_id = 1 WHERE currency_id IS NULL")
            print("Установлена валюта по умолчанию для существующих сделок")
        else:
            print("Колонка currency_id уже существует")
        
        cursor.close()
        conn.close()
        print("Миграция завершена успешно")
        
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        raise

if __name__ == "__main__":
    migrate_production_database() 