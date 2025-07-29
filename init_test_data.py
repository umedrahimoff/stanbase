#!/usr/bin/env python3
"""
Скрипт для инициализации тестовых данных в базе данных Stanbase.
Запускайте этот скрипт только при необходимости создания тестовых данных.
"""

from db import SessionLocal, Base, engine
from models import Company, Investor, News, Podcast, Job, Event, Deal, User, Person, Country, City, Category, Author, PortfolioEntry, CompanyStage, Feedback, EmailTemplate
from datetime import date, datetime, timedelta
from sqlalchemy import func
from utils.security import get_password_hash
import os
import sys

def create_test_data():
    """Создает тестовые данные в базе данных"""
    
    # Проверяем переменную окружения
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        print("❌ ОШИБКА: Создание тестовых данных запрещено в продакшене!")
        print("Установите ENVIRONMENT=development или ENVIRONMENT=staging для создания тестовых данных.")
        print("Или удалите переменную ENVIRONMENT для использования development по умолчанию.")
        sys.exit(1)
    
    print(f"🔧 Среда выполнения: {environment}")
    print("Начинаем создание тестовых данных...")
    
    # Создать все таблицы
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    try:
        # --- Страны ---
        if not session.query(Country).first():
            print("Создаем страны...")
            countries = [Country(name=n) for n in ["Казахстан", "Узбекистан", "Кыргызстан", "Таджикистан", "Туркменистан"]]
            session.add_all(countries)
            session.commit()
            print(f"Создано {len(countries)} стран")
        
        country_dict = {c.name: c.id for c in session.query(Country).all()}
        kz_id = country_dict.get("Казахстан") or list(country_dict.values())[0]
        
        # --- Города ---
        if not session.query(City).first():
            print("Создаем города...")
            cities = [City(name=n, country_id=kz_id) for n in ["Алматы", "Астана", "Ташкент", "Бишкек", "Душанбе"]]
            session.add_all(cities)
            session.commit()
            print(f"Создано {len(cities)} городов")
        
        # --- Категории ---
        if not session.query(Category).first():
            print("Создаем категории...")
            categories = [Category(name=n) for n in ["Fintech", "HealthTech", "HRTech", "E-commerce", "SaaS"]]
            session.add_all(categories)
            session.commit()
            print(f"Создано {len(categories)} категорий")
        
        # --- Компании ---
        if not session.query(Company).first():
            print("Создаем компании...")
            companies = [
                Company(name="CerebraAI", description="Платформа на базе искусственного интеллекта для диагностики инсульта и других заболеваний по КТ/МРТ. Используется более чем в 50 больницах, финалист TechCrunch Battlefield.", country="Казахстан", city="Алматы", stage="Growth", industry="HealthTech", website="https://cerebraai.ai"),
                Company(name="Uzum", description="Крупнейшая цифровая экосистема в Узбекистане: маркетплейс, финтех, BNPL, логистика, онлайн-банк. Более 15 млн пользователей.", country="Узбекистан", city="Ташкент", stage="Scale", industry="E-commerce, Fintech", website="https://uzum.com"),
                Company(name="Tezbus", description="Skyscanner для междугородних такси, автобусов и поездов в Центральной Азии. Онлайн-бронирование билетов, интеграция с перевозчиками.", country="Кыргызстан", city="Бишкек", stage="Seed", industry="Mobility, IT", website="http://www.tezbus.com"),
                Company(name="Voicy", description="AI для распознавания речи на казахском, узбекском, кыргызском языках. Используется для автоматизации call-центров и госуслуг.", country="Казахстан", city="Алматы", stage="Growth", industry="AI, NLP", website="https://voicy.tech"),
                Company(name="FORBOSSINFO", description="Первая мультисервисная платформа для бизнеса в Центральной Азии.", country="Казахстан", city="Алматы", stage="Seed", industry="Marketplace, B2B", website="https://www.forbossinfo.com"),
                Company(name="Pamir Group OÜ", description="Поставщик промышленного и энергетического оборудования, внедрение решений для зеленой энергетики и водорода.", country="Таджикистан", city="Душанбе", stage="Growth", industry="Energy, Industrial", website="https://pamirgp.com"),
                Company(name="BILLZ", description="Программа для магазина, складского и товарного учёта, автоматизации продаж.", country="Казахстан", city="Алматы", stage="Growth", industry="SaaS, RetailTech", website="https://billz.io/")
            ]
            session.add_all(companies)
            session.commit()
            print(f"Создано {len(companies)} компаний")
        
        # --- Новости ---
        if not session.query(News).first():
            print("Создаем новости...")
            news = [
                News(title="CerebraAI вошла в топ-200 стартапов TechCrunch Battlefield", summary="Казахстанский HealthTech-стартап получил международное признание.", date="2024-06-01", content="CerebraAI, ведущий AI-стартап в сфере медицины, вошёл в топ-200 стартапов TechCrunch Battlefield.", status="active"),
                News(title="Uzum привлек $50 млн инвестиций и стал первым единорогом Узбекистана", summary="Оценка Uzum превысила $1 млрд — это первый единорог страны.", date="2024-05-15", content="Экосистема Uzum объявила о привлечении $50 млн и достижении оценки $1 млрд.", status="active"),
                News(title="Tezbus запустил онлайн-бронирование билетов в Кыргызстане", summary="Tezbus расширяет сервисы по всей Центральной Азии.", date="2024-04-20", content="Tezbus Group запустила новый сервис для онлайн-бронирования междугородних поездок.", status="active"),
                News(title="Voicy внедряет распознавание казахской речи в госуслугах", summary="Voicy помогает цифровизации госуслуг в Казахстане.", date="2024-04-10", content="Voicy интегрировала свою AI-платформу в ряд государственных сервисов Казахстана.", status="active"),
                News(title="FORBOSSINFO запускает мультисервисную платформу для бизнеса в ЦА", summary="FORBOSSINFO выходит на рынок Казахстана и Узбекистана.", date="2024-03-01", content="FORBOSSINFO — первая мультисервисная платформа для бизнеса в Центральной Азии, стартовала в Казахстане.", status="active"),
                News(title="Pamir Group внедряет водородные технологии в Таджикистане", summary="Pamir Group реализует проекты по зелёной энергетике.", date="2024-02-15", content="Pamir Group OÜ внедряет решения по производству зелёного водорода и модернизации энергетики Таджикистана.", status="active")
            ]
            session.add_all(news)
            session.commit()
            print(f"Создано {len(news)} новостей")
        
        # --- Пользователи ---
        if not session.query(User).filter_by(email="admin@stanbase.test").first():
            print("Создаем тестовых пользователей...")
            admin_user = User(
                email="admin@stanbase.test", 
                password=get_password_hash("admin123"), 
                role="admin", 
                first_name="Admin", 
                last_name="Stanbase", 
                country_id=kz_id, 
                city="Алматы", 
                phone="+77001234567", 
                status="active"
            )
            session.add(admin_user)
            
            moderator_user = User(
                email="moderator@stanbase.test", 
                password=get_password_hash("mod123"), 
                role="moderator", 
                first_name="Mod", 
                last_name="Stanbase", 
                country_id=kz_id, 
                city="Алматы", 
                phone="+77001234568", 
                status="active"
            )
            session.add(moderator_user)
            
            companies = session.query(Company).all()
            if companies:
                startuper_user = User(
                    email="startuper@stanbase.test", 
                    password=get_password_hash("startuper123"), 
                    role="startuper", 
                    first_name="Start", 
                    last_name="Stanbase", 
                    country_id=kz_id, 
                    city="Алматы", 
                    phone="+77001234569", 
                    company_id=companies[0].id, 
                    status="active"
                )
                session.add(startuper_user)
            
            session.commit()
            print("Создано 3 тестовых пользователя")
        
        # --- Email шаблоны ---
        if not session.query(EmailTemplate).first():
            print("Создаем email шаблоны...")
            email_templates = [
                {
                    "name": "Приветственное письмо",
                    "code": "welcome",
                    "subject": "Добро пожаловать в Stanbase!",
                    "html_content": """<h2>Добро пожаловать в Stanbase!</h2>
<p>Здравствуйте, {{ user_name }}!</p>
<p>Спасибо за регистрацию в Stanbase - платформе для стартапов и инвесторов Центральной Азии.</p>
<p>Теперь вы можете:</p>
<ul>
<li>Создавать профили компаний</li>
<li>Находить инвесторов</li>
<li>Публиковать новости</li>
<li>Участвовать в событиях</li>
</ul>
<p>С уважением,<br>Команда Stanbase</p>""",
                    "text_content": """Добро пожаловать в Stanbase!

Здравствуйте, {{ user_name }}!

Спасибо за регистрацию в Stanbase - платформе для стартапов и инвесторов Центральной Азии.

Теперь вы можете:
- Создавать профили компаний
- Находить инвесторов
- Публиковать новости
- Участвовать в событиях

С уважением,
Команда Stanbase""",
                    "description": "Отправляется при регистрации нового пользователя",
                    "variables": '{"user_name": "Имя пользователя"}'
                },
                {
                    "name": "Восстановление пароля",
                    "code": "password_reset",
                    "subject": "Сброс пароля - Stanbase",
                    "html_content": """<h2>Сброс пароля</h2>
<p>Здравствуйте!</p>
<p>Вы запросили сброс пароля для вашего аккаунта в Stanbase.</p>
<p>Нажмите на кнопку ниже для сброса пароля:</p>
<p><a href="{{ reset_url }}">Сбросить пароль</a></p>
<p>Если кнопка не работает, скопируйте ссылку в браузер:</p>
<p>{{ reset_url }}</p>
<p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
<p>Ссылка действительна в течение 30 минут.</p>
<p>С уважением,<br>Команда Stanbase</p>""",
                    "text_content": """Сброс пароля

Здравствуйте!

Вы запросили сброс пароля для вашего аккаунта в Stanbase.

Перейдите по ссылке:
{{ reset_url }}

Если вы не запрашивали сброс пароля, проигнорируйте это письмо.

Ссылка действительна в течение 30 минут.

С уважением,
Команда Stanbase""",
                    "description": "Отправляется при запросе сброса пароля",
                    "variables": '{"reset_url": "Ссылка для сброса пароля"}'
                }
            ]
            
            for template_data in email_templates:
                template = EmailTemplate(
                    name=template_data["name"],
                    code=template_data["code"],
                    subject=template_data["subject"],
                    html_content=template_data["html_content"],
                    text_content=template_data["text_content"],
                    description=template_data["description"],
                    variables=template_data["variables"],
                    is_active=True
                )
                session.add(template)
            session.commit()
            print(f"Создано {len(email_templates)} email шаблонов")
        
        print("✅ Тестовые данные успешно созданы!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_test_data()