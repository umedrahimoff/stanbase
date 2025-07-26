import psycopg2
import os
from datetime import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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
        
        # Проверяем существование колонки views в таблице news
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'news' AND column_name = 'views'
            );
        """)
        
        views_exists = cursor.fetchone()[0]
        
        if not views_exists:
            print("Добавляем колонку views в таблицу news...")
            cursor.execute("""
                ALTER TABLE news ADD COLUMN views INTEGER DEFAULT 0;
            """)
            print("Колонка views добавлена в таблицу news")
        else:
            print("Колонка views уже существует в таблице news")
            
            # Проверяем существование колонки seo_description в таблице news
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'news' AND column_name = 'seo_description'
                );
            """)
            
            seo_description_exists = cursor.fetchone()[0]
            
            if not seo_description_exists:
                print("Добавляем колонку seo_description в таблицу news...")
                cursor.execute("""
                    ALTER TABLE news ADD COLUMN seo_description VARCHAR(512);
                """)
                print("Колонка seo_description добавлена в таблицу news")
            else:
                print("Колонка seo_description уже существует в таблице news")
            
            # Проверяем существование колонки image в таблице news
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'news' AND column_name = 'image'
                );
            """)
            
            image_exists = cursor.fetchone()[0]
            
            if not image_exists:
                print("Добавляем колонку image в таблицу news...")
                cursor.execute("""
                    ALTER TABLE news ADD COLUMN image VARCHAR(256);
                """)
                print("Колонка image добавлена в таблицу news")
            else:
                print("Колонка image уже существует в таблице news")
            
            # Проверяем существование колонки created_at в таблице news
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'news' AND column_name = 'created_at'
                );
            """)
            
            created_at_exists = cursor.fetchone()[0]
            
            if not created_at_exists:
                print("Добавляем колонку created_at в таблицу news...")
                cursor.execute("""
                    ALTER TABLE news ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """)
                print("Колонка created_at добавлена в таблицу news")
            else:
                print("Колонка created_at уже существует в таблице news")
            
            # Проверяем существование колонки updated_at в таблице news
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'news' AND column_name = 'updated_at'
                );
            """)
            
            updated_at_exists = cursor.fetchone()[0]
            
            if not updated_at_exists:
                print("Добавляем колонку updated_at в таблицу news...")
                cursor.execute("""
                    ALTER TABLE news ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """)
                print("Колонка updated_at добавлена в таблицу news")
            else:
                print("Колонка updated_at уже существует в таблице news")
            
            # Проверяем существование колонки created_by в таблице news
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'news' AND column_name = 'created_by'
                );
            """)
            
            created_by_exists = cursor.fetchone()[0]
            
            if not created_by_exists:
                print("Добавляем колонку created_by в таблицу news...")
                cursor.execute("""
                    ALTER TABLE news ADD COLUMN created_by VARCHAR(64);
                """)
                print("Колонка created_by добавлена в таблицу news")
            else:
                print("Колонка created_by уже существует в таблице news")
            
            # Проверяем существование колонки updated_by в таблице news
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'news' AND column_name = 'updated_by'
                );
            """)
            
            updated_by_exists = cursor.fetchone()[0]
            
            if not updated_by_exists:
                print("Добавляем колонку updated_by в таблицу news...")
                cursor.execute("""
                    ALTER TABLE news ADD COLUMN updated_by VARCHAR(64);
                """)
                print("Колонка updated_by добавлена в таблицу news")
            else:
                print("Колонка updated_by уже существует в таблице news")
            
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

def run_migration():
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Подключение к базе данных успешно установлено")
        
        # Проверяем, существуют ли уже поля pitch и pitch_date
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'company' 
            AND column_name IN ('pitch', 'pitch_date')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Добавляем поле pitch, если его нет
        if 'pitch' not in existing_columns:
            print("Добавляем поле 'pitch'...")
            cursor.execute("ALTER TABLE company ADD COLUMN pitch VARCHAR(256)")
            print("Поле 'pitch' добавлено успешно")
        else:
            # Изменяем тип поля pitch на VARCHAR(256) если оно существует как TEXT
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'company' 
                AND column_name = 'pitch'
            """)
            current_type = cursor.fetchone()[0]
            if current_type == 'text':
                print("Изменяем тип поля 'pitch' с TEXT на VARCHAR(256)...")
                cursor.execute("ALTER TABLE company ALTER COLUMN pitch TYPE VARCHAR(256)")
                print("Тип поля 'pitch' изменен успешно")
            else:
                print("Поле 'pitch' уже имеет правильный тип")
        
        # Добавляем поле pitch_date, если его нет
        if 'pitch_date' not in existing_columns:
            print("Добавляем поле 'pitch_date'...")
            cursor.execute("ALTER TABLE company ADD COLUMN pitch_date TIMESTAMP")
            print("Поле 'pitch_date' добавлено успешно")
        else:
            print("Поле 'pitch_date' уже существует")
        
        print("Миграция завершена успешно!")
        
    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    print("Начинаем миграцию базы данных...")
    success = run_migration()
    if success:
        print("Миграция выполнена успешно!")
    else:
        print("Миграция завершилась с ошибкой!")
        exit(1) 