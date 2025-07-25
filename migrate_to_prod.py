import psycopg2
import os
from datetime import datetime

# Данные для подключения к продакшн базе данных Render
DATABASE_URL = os.getenv('DATABASE_URL')

def migrate_production_database():
    """Выполняет миграции на продакшн базе данных"""
    
    # Получаем строку подключения из переменной окружения
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Ошибка: DATABASE_URL не найден в переменных окружения")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Подключение к базе данных установлено")
        
        # Проверяем существование таблицы currency
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'currency'
            );
        """)
        
        currency_exists = cursor.fetchone()[0]
        
        if not currency_exists:
            print("Создаем таблицу currency...")
            cursor.execute("""
                CREATE TABLE currency (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(8) UNIQUE NOT NULL,
                    name VARCHAR(64) NOT NULL,
                    symbol VARCHAR(8),
                    status VARCHAR(16) DEFAULT 'active'
                );
            """)
            
            # Добавляем базовые валюты
            cursor.execute("""
                INSERT INTO currency (code, name, symbol, status) VALUES
                ('USD', 'Доллар США', '$', 'active'),
                ('EUR', 'Евро', '€', 'active'),
                ('KZT', 'Тенге', '₸', 'active'),
                ('UZS', 'Сум', 'сум', 'active'),
                ('KGS', 'Сом', 'с', 'active'),
                ('TJS', 'Сомони', 'ЅМ', 'active'),
                ('TMT', 'Манат', 'T', 'active')
                ON CONFLICT (code) DO NOTHING;
            """)
            print("Таблица currency создана и заполнена данными")
        else:
            print("Таблица currency уже существует")
        
        # Проверяем существование колонки logo в таблице investor
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'investor' AND column_name = 'logo'
            );
        """)
        
        logo_exists = cursor.fetchone()[0]
        
        if not logo_exists:
            print("Добавляем колонку logo в таблицу investor...")
            cursor.execute("""
                ALTER TABLE investor ADD COLUMN logo VARCHAR(256);
            """)
            print("Колонка logo добавлена в таблицу investor")
        else:
            print("Колонка logo уже существует в таблице investor")
        
        # Проверяем существование колонки currency_id в таблице deal
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'deal' AND column_name = 'currency_id'
            );
        """)
        
        currency_id_exists = cursor.fetchone()[0]
        
        if not currency_id_exists:
            print("Добавляем колонку currency_id в таблицу deal...")
            cursor.execute("""
                ALTER TABLE deal ADD COLUMN currency_id INTEGER REFERENCES currency(id);
            """)
            
            # Обновляем существующие сделки, устанавливая USD как валюту по умолчанию
            cursor.execute("""
                UPDATE deal SET currency_id = (SELECT id FROM currency WHERE code = 'USD' LIMIT 1)
                WHERE currency_id IS NULL;
            """)
            print("Колонка currency_id добавлена в таблицу deal и обновлена")
        else:
            print("Колонка currency_id уже существует в таблице deal")
        
        # Проверяем существование колонки slug в таблице news
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'news' AND column_name = 'slug'
            );
        """)
        
        slug_exists = cursor.fetchone()[0]
        
        if not slug_exists:
            print("Добавляем колонку slug в таблицу news...")
            cursor.execute("""
                ALTER TABLE news ADD COLUMN slug VARCHAR(256) UNIQUE;
            """)
            print("Колонка slug добавлена в таблицу news")
        else:
            print("Колонка slug уже существует в таблице news")
        
        # Фиксируем изменения
        conn.commit()
        print("Миграция успешно выполнена!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    migrate_production_database() 