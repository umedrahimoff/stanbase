import json
import psycopg2
import os
from datetime import datetime

def import_data_to_production(json_file):
    """Импорт данных из JSON файла в продакшн PostgreSQL базу"""
    
    # Загрузка данных из JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    import_data_from_dict(data)

def import_data_from_dict(data):
    """Импорт данных из словаря в продакшн PostgreSQL базу"""
    
    # Подключение к продакшн базе
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("Ошибка: DATABASE_URL не установлен")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Отключаем автокоммит для транзакций
        cursor = conn.cursor()
        
        print("Подключение к продакшн базе данных установлено")
        
        # Импорт валют
        print("Импортируем валюты...")
        for currency in data.get('currencies', []):
            cursor.execute("""
                INSERT INTO currency (id, code, name, symbol, status) 
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    code = EXCLUDED.code,
                    name = EXCLUDED.name,
                    symbol = EXCLUDED.symbol,
                    status = EXCLUDED.status
            """, (currency['id'], currency['code'], currency['name'], currency['symbol'], currency['status']))
        print(f"Импортировано валют: {len(data.get('currencies', []))}")
        
        # Импорт стран
        print("Импортируем страны...")
        for country in data.get('countries', []):
            cursor.execute("""
                INSERT INTO country (id, name, code, status) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    code = EXCLUDED.code,
                    status = EXCLUDED.status
            """, (country['id'], country['name'], country['code'], country['status']))
        print(f"Импортировано стран: {len(data.get('countries', []))}")
        
        # Импорт городов
        print("Импортируем города...")
        for city in data.get('cities', []):
            cursor.execute("""
                INSERT INTO city (id, name, country_id, status) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    country_id = EXCLUDED.country_id,
                    status = EXCLUDED.status
            """, (city['id'], city['name'], city['country_id'], city['status']))
        print(f"Импортировано городов: {len(data.get('cities', []))}")
        
        # Импорт категорий
        print("Импортируем категории...")
        for category in data.get('categories', []):
            cursor.execute("""
                INSERT INTO category (id, name, description, status) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status
            """, (category['id'], category['name'], category.get('description'), category['status']))
        print(f"Импортировано категорий: {len(data.get('categories', []))}")
        
        # Импорт компаний
        print("Импортируем компании...")
        for company in data.get('companies', []):
            cursor.execute("""
                INSERT INTO company (id, name, description, website, country_id, city_id, 
                                   industry, stage, founded_year, logo, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    website = EXCLUDED.website,
                    country_id = EXCLUDED.country_id,
                    city_id = EXCLUDED.city_id,
                    industry = EXCLUDED.industry,
                    stage = EXCLUDED.stage,
                    founded_year = EXCLUDED.founded_year,
                    logo = EXCLUDED.logo,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                company['id'], company['name'], company.get('description'), 
                company.get('website'), company.get('country_id'), company.get('city_id'),
                company.get('industry'), company.get('stage'), company.get('founded_year'),
                company.get('logo'), company['status'], company.get('created_at'), 
                company.get('updated_at')
            ))
        print(f"Импортировано компаний: {len(data.get('companies', []))}")
        
        # Импорт инвесторов
        print("Импортируем инвесторов...")
        for investor in data.get('investors', []):
            cursor.execute("""
                INSERT INTO investor (id, name, description, website, country_id, city_id, 
                                    type, logo, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    website = EXCLUDED.website,
                    country_id = EXCLUDED.country_id,
                    city_id = EXCLUDED.city_id,
                    type = EXCLUDED.type,
                    logo = EXCLUDED.logo,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                investor['id'], investor['name'], investor.get('description'), 
                investor.get('website'), investor.get('country_id'), investor.get('city_id'),
                investor.get('type'), investor.get('logo'), investor['status'], 
                investor.get('created_at'), investor.get('updated_at')
            ))
        print(f"Импортировано инвесторов: {len(data.get('investors', []))}")
        
        # Импорт сделок
        print("Импортируем сделки...")
        for deal in data.get('deals', []):
            cursor.execute("""
                INSERT INTO deal (id, type, amount, valuation, date, company_id, 
                                investors, currency_id, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    type = EXCLUDED.type,
                    amount = EXCLUDED.amount,
                    valuation = EXCLUDED.valuation,
                    date = EXCLUDED.date,
                    company_id = EXCLUDED.company_id,
                    investors = EXCLUDED.investors,
                    currency_id = EXCLUDED.currency_id,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                deal['id'], deal.get('type'), deal.get('amount'), deal.get('valuation'),
                deal.get('date'), deal.get('company_id'), deal.get('investors'),
                deal.get('currency_id'), deal['status'], deal.get('created_at'), 
                deal.get('updated_at')
            ))
        print(f"Импортировано сделок: {len(data.get('deals', []))}")
        
        # Импорт людей
        print("Импортируем людей...")
        for person in data.get('people', []):
            cursor.execute("""
                INSERT INTO person (id, name, country, linkedin, role, status) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    country = EXCLUDED.country,
                    linkedin = EXCLUDED.linkedin,
                    role = EXCLUDED.role,
                    status = EXCLUDED.status
            """, (
                person['id'], person['name'], person.get('country'), 
                person.get('linkedin'), person.get('role'), person['status']
            ))
        print(f"Импортировано людей: {len(data.get('people', []))}")
        
        # Импорт вакансий
        print("Импортируем вакансии...")
        for job in data.get('jobs', []):
            cursor.execute("""
                INSERT INTO job (id, title, description, company_id, location, 
                               salary_min, salary_max, requirements, contact, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    company_id = EXCLUDED.company_id,
                    location = EXCLUDED.location,
                    salary_min = EXCLUDED.salary_min,
                    salary_max = EXCLUDED.salary_max,
                    requirements = EXCLUDED.requirements,
                    contact = EXCLUDED.contact,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                job['id'], job['title'], job.get('description'), job.get('company_id'),
                job.get('location'), job.get('salary_min'), job.get('salary_max'),
                job.get('requirements'), job.get('contact'), job['status'],
                job.get('created_at'), job.get('updated_at')
            ))
        print(f"Импортировано вакансий: {len(data.get('jobs', []))}")
        
        # Импорт новостей
        print("Импортируем новости...")
        for news_item in data.get('news', []):
            cursor.execute("""
                INSERT INTO news (id, title, content, source, url, date, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    source = EXCLUDED.source,
                    url = EXCLUDED.url,
                    date = EXCLUDED.date,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                news_item['id'], news_item['title'], news_item.get('content'),
                news_item.get('source'), news_item.get('url'), news_item.get('date'),
                news_item['status'], news_item.get('created_at'), news_item.get('updated_at')
            ))
        print(f"Импортировано новостей: {len(data.get('news', []))}")
        
        # Импорт мероприятий
        print("Импортируем мероприятия...")
        for event in data.get('events', []):
            cursor.execute("""
                INSERT INTO event (id, title, description, date, location, url, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    date = EXCLUDED.date,
                    location = EXCLUDED.location,
                    url = EXCLUDED.url,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                event['id'], event['title'], event.get('description'), event.get('date'),
                event.get('location'), event.get('url'), event['status'],
                event.get('created_at'), event.get('updated_at')
            ))
        print(f"Импортировано мероприятий: {len(data.get('events', []))}")
        
        # Импорт подкастов
        print("Импортируем подкасты...")
        for podcast in data.get('podcasts', []):
            cursor.execute("""
                INSERT INTO podcast (id, title, description, url, date, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    url = EXCLUDED.url,
                    date = EXCLUDED.date,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                podcast['id'], podcast['title'], podcast.get('description'),
                podcast.get('url'), podcast.get('date'), podcast['status'],
                podcast.get('created_at'), podcast.get('updated_at')
            ))
        print(f"Импортировано подкастов: {len(data.get('podcasts', []))}")
        
        # Импорт связей компания-человек
        print("Импортируем связи компания-человек...")
        for link in data.get('startup_person', []):
            cursor.execute("""
                INSERT INTO company_person (company_id, person_id) 
                VALUES (%s, %s)
                ON CONFLICT (company_id, person_id) DO NOTHING
            """, (link['company_id'], link['person_id']))
        print(f"Импортировано связей компания-человек: {len(data.get('startup_person', []))}")
        
        # Импорт связей инвестор-компания
        print("Импортируем связи инвестор-компания...")
        for link in data.get('investor_startup', []):
            cursor.execute("""
                INSERT INTO investor_company (investor_id, company_id) 
                VALUES (%s, %s)
                ON CONFLICT (investor_id, company_id) DO NOTHING
            """, (link['investor_id'], link['company_id']))
        print(f"Импортировано связей инвестор-компания: {len(data.get('investor_startup', []))}")
        
        # Импорт пользователей
        print("Импортируем пользователей...")
        for user in data.get('users', []):
            cursor.execute("""
                INSERT INTO "user" (id, email, password_hash, role, status, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET 
                    email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """, (
                user['id'], user['email'], user['password_hash'], user['role'],
                user['status'], user.get('created_at'), user.get('updated_at')
            ))
        print(f"Импортировано пользователей: {len(data.get('users', []))}")
        
        # Коммит всех изменений
        conn.commit()
        print("\nИмпорт завершен успешно!")
        
    except Exception as e:
        print(f"Ошибка при импорте: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Найти последний файл экспорта
    export_files = [f for f in os.listdir('.') if f.startswith('export_data_') and f.endswith('.json')]
    if not export_files:
        print("Файл экспорта не найден. Сначала запустите export_data.py")
        exit(1)
    
    latest_file = max(export_files)
    print(f"Импортируем данные из файла: {latest_file}")
    
    import_data_to_production(latest_file) 