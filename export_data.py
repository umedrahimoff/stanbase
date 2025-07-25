import json
import sqlite3
from datetime import datetime
import os

def export_data():
    """Экспорт всех данных из локальной SQLite базы в JSON"""
    
    # Подключение к локальной базе
    conn = sqlite3.connect('instance/stanbase.db')
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени
    cursor = conn.cursor()
    
    data = {}
    
    # Экспорт валют
    print("Экспортируем валюты...")
    cursor.execute("SELECT * FROM currency")
    currencies = [dict(row) for row in cursor.fetchall()]
    data['currencies'] = currencies
    print(f"Экспортировано валют: {len(currencies)}")
    
    # Экспорт стран
    print("Экспортируем страны...")
    cursor.execute("SELECT * FROM country")
    countries = [dict(row) for row in cursor.fetchall()]
    data['countries'] = countries
    print(f"Экспортировано стран: {len(countries)}")
    
    # Экспорт городов
    print("Экспортируем города...")
    cursor.execute("SELECT * FROM city")
    cities = [dict(row) for row in cursor.fetchall()]
    data['cities'] = cities
    print(f"Экспортировано городов: {len(cities)}")
    
    # Экспорт категорий
    print("Экспортируем категории...")
    cursor.execute("SELECT * FROM category")
    categories = [dict(row) for row in cursor.fetchall()]
    data['categories'] = categories
    print(f"Экспортировано категорий: {len(categories)}")
    
    # Экспорт стадий
    print("Экспортируем стадии...")
    cursor.execute("SELECT * FROM company_stage")
    stages = [dict(row) for row in cursor.fetchall()]
    data['stages'] = stages
    print(f"Экспортировано стадий: {len(stages)}")
    
    # Экспорт компаний
    print("Экспортируем компании...")
    cursor.execute("SELECT * FROM company")
    companies = [dict(row) for row in cursor.fetchall()]
    data['companies'] = companies
    print(f"Экспортировано компаний: {len(companies)}")
    
    # Экспорт инвесторов
    print("Экспортируем инвесторов...")
    cursor.execute("SELECT * FROM investor")
    investors = [dict(row) for row in cursor.fetchall()]
    data['investors'] = investors
    print(f"Экспортировано инвесторов: {len(investors)}")
    
    # Экспорт сделок
    print("Экспортируем сделки...")
    cursor.execute("SELECT * FROM deal")
    deals = [dict(row) for row in cursor.fetchall()]
    data['deals'] = deals
    print(f"Экспортировано сделок: {len(deals)}")
    
    # Экспорт людей
    print("Экспортируем людей...")
    cursor.execute("SELECT * FROM person")
    people = [dict(row) for row in cursor.fetchall()]
    data['people'] = people
    print(f"Экспортировано людей: {len(people)}")
    
    # Экспорт вакансий
    print("Экспортируем вакансии...")
    cursor.execute("SELECT * FROM job")
    jobs = [dict(row) for row in cursor.fetchall()]
    data['jobs'] = jobs
    print(f"Экспортировано вакансий: {len(jobs)}")
    
    # Экспорт новостей
    print("Экспортируем новости...")
    cursor.execute("SELECT * FROM news")
    news = [dict(row) for row in cursor.fetchall()]
    data['news'] = news
    print(f"Экспортировано новостей: {len(news)}")
    
    # Экспорт мероприятий
    print("Экспортируем мероприятия...")
    cursor.execute("SELECT * FROM event")
    events = [dict(row) for row in cursor.fetchall()]
    data['events'] = events
    print(f"Экспортировано мероприятий: {len(events)}")
    
    # Экспорт подкастов
    print("Экспортируем подкасты...")
    cursor.execute("SELECT * FROM podcast")
    podcasts = [dict(row) for row in cursor.fetchall()]
    data['podcasts'] = podcasts
    print(f"Экспортировано подкастов: {len(podcasts)}")
    
    # Экспорт связей компания-человек
    print("Экспортируем связи компания-человек...")
    cursor.execute("SELECT * FROM company_person")
    startup_person = [dict(row) for row in cursor.fetchall()]
    data['startup_person'] = startup_person
    print(f"Экспортировано связей компания-человек: {len(startup_person)}")
    
    # Экспорт связей инвестор-человек
    print("Экспортируем связи инвестор-человек...")
    cursor.execute("SELECT * FROM investor_person")
    investor_person = [dict(row) for row in cursor.fetchall()]
    data['investor_person'] = investor_person
    print(f"Экспортировано связей инвестор-человек: {len(investor_person)}")
    
    # Экспорт связей инвестор-компания
    print("Экспортируем связи инвестор-компания...")
    cursor.execute("SELECT * FROM investor_company")
    investor_startup = [dict(row) for row in cursor.fetchall()]
    data['investor_startup'] = investor_startup
    print(f"Экспортировано связей инвестор-компания: {len(investor_startup)}")
    
    # Экспорт связей компания-стадия
    print("Экспортируем связи компания-стадия...")
    cursor.execute("SELECT * FROM company_stage")
    startup_stage = [dict(row) for row in cursor.fetchall()]
    data['startup_stage'] = startup_stage
    print(f"Экспортировано связей компания-стадия: {len(startup_stage)}")
    
    # Экспорт портфолио
    print("Экспортируем портфолио...")
    cursor.execute("SELECT * FROM portfolio_entry")
    portfolio_entries = [dict(row) for row in cursor.fetchall()]
    data['portfolio_entries'] = portfolio_entries
    print(f"Экспортировано записей портфолио: {len(portfolio_entries)}")
    
    # Экспорт авторов
    print("Экспортируем авторов...")
    cursor.execute("SELECT * FROM author")
    authors = [dict(row) for row in cursor.fetchall()]
    data['authors'] = authors
    print(f"Экспортировано авторов: {len(authors)}")
    
    # Экспорт пользователей
    print("Экспортируем пользователей...")
    cursor.execute("SELECT * FROM user")
    users = [dict(row) for row in cursor.fetchall()]
    data['users'] = users
    print(f"Экспортировано пользователей: {len(users)}")
    
    conn.close()
    
    # Сохранение в файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_data_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\nЭкспорт завершен! Данные сохранены в файл: {filename}")
    print(f"Общий размер файла: {os.path.getsize(filename) / 1024:.1f} KB")
    
    return filename

if __name__ == "__main__":
    export_data() 