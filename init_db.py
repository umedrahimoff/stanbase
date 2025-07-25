from db import Base, engine, SessionLocal
import models
from models import *
from datetime import date, datetime, timedelta
from sqlalchemy import func

# Создать все таблицы
Base.metadata.create_all(bind=engine)

# Заполнить тестовыми данными, если база пуста
session = SessionLocal()

# --- Вымышленные компании ЦА ---
ca_countries = [
    ("Казахстан", ["Алматы", "Астана", "Шымкент", "Караганда", "Актобе"]),
    ("Узбекистан", ["Ташкент", "Самарканд", "Бухара", "Наманган", "Андижан"]),
    ("Кыргызстан", ["Бишкек", "Ош", "Джалал-Абад", "Каракол", "Токмок"]),
    ("Таджикистан", ["Душанбе", "Худжанд", "Бохтар", "Куляб", "Истаравшан"]),
    ("Туркменистан", ["Ашхабад", "Туркменабад", "Дашогуз", "Мары", "Балканабад"])
]
industries = ["Fintech", "SaaS", "AgriTech", "HealthTech", "Mobility", "CleanTech", "AI", "EdTech", "RetailTech", "LogisticsTech"]
stages = ["Seed", "Growth", "Scale", "Series A", "Series B"]

# Вымышленные названия компаний без географических привязок
company_names = [
    "TechFlow Labs", "InnovateHub", "DigitalBridge", "SmartCore", "FutureTech",
    "CloudMatrix", "DataVault", "GreenSolutions", "MobileFirst", "AI Nexus",
    "EduTech Pro", "RetailSmart", "LogiTech", "HealthSync", "AgroTech"
]

# Технопарки по странам
tech_parks = {
    "Казахстан": ["Astana Hub 🇰🇿", "Almaty Tech Garden 🇰🇿"],
    "Узбекистан": ["IT Park 🇺🇿", "Tashkent Tech Hub 🇺🇿"],
    "Кыргызстан": ["ПВТ 🇰🇬", "Bishkek Tech Park 🇰🇬"],
    "Таджикистан": ["IT Park 🇹🇯", "Dushanbe Tech Hub 🇹🇯"],
    "Туркменистан": ["Ashgabat Tech 🇹🇲", "Turkmen Tech Hub 🇹🇲"]
}

companies_data = []
for i in range(15):
    country, cities = ca_countries[i % len(ca_countries)]
    city = cities[i % len(cities)]
    industry = industries[i % len(industries)]
    stage = stages[i % len(stages)]
    name = company_names[i]
    # Выбираем случайный технопарк для страны
    country_parks = tech_parks.get(country, [])
    tech_park = country_parks[i % len(country_parks)] if country_parks else None
    companies_data.append({
        "name": name,
        "description": f"Ведущий проект в сфере {industry.lower()} для региона.",
        "country": country,
        "city": city,
        "stage": stage,
        "industry": industry,
        "website": f"https://{name.lower().replace(' ', '')}.com",
        "tech_park": tech_park
    })

# Вымышленные названия фондов без географических привязок
fund_names = [
    "Steppe Angels", "Turan Ventures", "UzStart Capital", "Bishkek Angels", "Samarkand Fund",
    "Dushanbe Capital", "Ashgabat Ventures", "Kyrgyz Fund", "Tajik Capital", "Uzbek Angels",
    "Central Asia Fund", "Silk Road Ventures", "Nomad Capital", "Oasis Fund", "Desert Angels"
]

funds_data = []
for i in range(15):
    country, _ = ca_countries[i % len(ca_countries)]
    type_ = "angel" if i % 2 == 0 else "venture"
    focus = ", ".join([industries[(i+j)%len(industries)] for j in range(2)])
    name = fund_names[i]
    funds_data.append({
        "name": name,
        "description": f"{type_.capitalize()} фонд для поддержки {focus}.",
        "country": country,
        "focus": focus,
        "stages": ", ".join(stages[:2]),
        "website": f"https://{name.lower().replace(' ', '')}.com",
        "type": type_
    })

# --- Компании ---
if not session.query(Company).first():
    for s in companies_data:
        company = Company(
            name=s["name"],
            description=s["description"],
            country=s["country"],
            city=s["city"],
            stage=s["stage"],
            industry=s["industry"],
            founded_date=date(2020, 1, 1),
            website=s["website"],
            tech_park=s["tech_park"]
        )
        session.add(company)
    session.commit()

company_objs = session.query(Company).all()

# --- Инвесторы ---
if not session.query(Investor).first():
    for f in funds_data:
        investor = Investor(
            name=f["name"],
            description=f["description"],
            country=f["country"],
            focus=f["focus"],
            stages=f["stages"],
            website=f["website"],
            type=f["type"]
        )
        session.add(investor)
    session.commit()

investor_objs = session.query(Investor).all()

# --- Команды компаний ---
team_roles = ["CEO", "CTO", "COO", "CMO", "Product Manager", "Lead Engineer", "HR", "Designer", "QA", "Data Scientist", "DevOps", "Sales", "Support", "Growth", "Finance"]
for i, company in enumerate(company_objs):
    if not company.team:
        for j in range(3):
            p = Person(name=f"Person {i*3+j+1}", role=team_roles[(i*3+j)%len(team_roles)], country=company.country)
            session.add(p)
            company.team.append(p)
session.commit()

# --- Вакансии для каждой компании ---
if not session.query(Job).first():
    job_titles = ["Backend Developer", "Frontend Developer", "Product Manager", "Data Scientist", "QA Engineer", "DevOps", "UI/UX Designer", "Sales Manager", "Support Specialist", "HR Manager", "Business Analyst", "Growth Hacker", "Finance Analyst", "Content Manager", "Marketing Specialist"]
    for i, company in enumerate(company_objs):
        session.add(Job(
            title=job_titles[i % len(job_titles)],
            description="Работа в инновационной команде. Гибкий график, международные проекты.",
            company_id=company.id,
            city=company.city,
            job_type="Full-time" if i % 2 == 0 else "Remote",
            contact=f"hr@{company.website.split('//')[1]}",
            status="active"
        ))
session.commit()

# --- Валюты ---
if not session.query(Currency).first():
    currencies = [
        Currency(code="USD", name="Доллар США", symbol="$", status="active"),
        Currency(code="EUR", name="Евро", symbol="€", status="active"),
        Currency(code="KZT", name="Тенге", symbol="₸", status="active"),
        Currency(code="RUB", name="Рубль", symbol="₽", status="active"),
        Currency(code="UZS", name="Сум", symbol="so'm", status="active"),
        Currency(code="GBP", name="Фунт стерлингов", symbol="£", status="active"),
        Currency(code="CNY", name="Юань", symbol="¥", status="active"),
    ]
    for currency in currencies:
        session.add(currency)
    session.commit()

# --- Сделки и портфели ---
if not session.query(Deal).first():
    usd = session.query(Currency).filter_by(code="USD").first()
    eur = session.query(Currency).filter_by(code="EUR").first()
    for i, company in enumerate(company_objs):
        invs = investor_objs[i % len(investor_objs): (i % len(investor_objs)) + 2]
        deal = Deal(
            type=stages[i % len(stages)],
            amount=500000 + i*100000,
            valuation=2000000 + i*500000,
            date=date(2023, 3, 15 + i),
            currency_id=usd.id if i % 2 == 0 else eur.id,
            company_id=company.id,
            investors=", ".join([inv.name for inv in invs]),
            status="active"
        )
        session.add(deal)
        for inv in invs:
            if company not in inv.portfolio:
                inv.portfolio.append(company)
session.commit()

# --- Новости ---
if not session.query(News).first():
    for i in range(15):
        company = company_objs[i % len(company_objs)]
        session.add(News(
            title=f"{company.name} анонсировал новый продукт {i+1}",
            summary=f"Краткое описание новости о {company.name} и инновациях.",
            date=date.today() - timedelta(days=i),
            content=f"Подробности о запуске, инвестициях и планах {company.name}.",
            status='active'
        ))
    session.commit()

# --- Подкасты ---
if not session.query(Podcast).first():
    for i in range(15):
        company = company_objs[i % len(company_objs)]
        session.add(Podcast(
            title=f"TechTalk {company.name} — выпуск {i+1}",
            description=f"Обсуждаем тренды и кейсы {company.name} и рынка.",
            youtube_url='https://www.youtube.com/embed/dQw4w9WgXcQ',
            date=date.today() - timedelta(days=i*2),
            status='active'
        ))
    session.commit()

# --- События ---
if not session.query(Event).first():
    for i in range(15):
        city = company_objs[i % len(company_objs)].city
        session.add(Event(
            title=f"Tech Event {city} {i+1}",
            description=f"Международное мероприятие по инновациям и технологиям в {city}.",
            date=datetime.now() + timedelta(days=i),
            format='Online' if i % 2 == 0 else 'Offline',
            location=city,
            registration_url=f'https://event{i+1}.com',
            status='active'
        ))
    session.commit()

# --- Тестовые пользователи ---
if not session.query(User).filter_by(email="admin@stanbase.test").first():
    admin_user = User(
        email="admin@stanbase.test",
        password="admin123",
        role="admin",
        first_name="Alice",
        last_name="Johnson",
        country_id=1,
        city="London",
        phone="+441234567890",
        status="active"
    )
    session.add(admin_user)
    session.commit()
if not session.query(User).filter_by(email="moderator@stanbase.test").first():
    moderator_user = User(
        email="moderator@stanbase.test",
        password="mod123",
        role="moderator",
        first_name="Bob",
        last_name="Smith",
        country_id=2,
        city="Berlin",
        phone="+491234567890",
        status="active"
    )
    session.add(moderator_user)
    session.commit()
if not session.query(User).filter_by(email="company_owner@stanbase.test").first():
    company = session.query(Company).first()
    if company:
        company_owner_user = User(
            email="company_owner@stanbase.test",
            password="company_owner123",
            role="company_owner",
            first_name="Charlie",
            last_name="Brown",
            country_id=3,
            city="Toronto",
            phone="+14161234567",
            company_id=company.id,
            status="active"
        )
        session.add(company_owner_user)
        session.commit()

# --- Исправление country, city, stage, industry для стартапов ---
def fix_company_fields():
    session = SessionLocal()
    from models import Company, Country, City, CompanyStage, Category
    companies = session.query(Company).all()
    for s in companies:
        # Исправить страну
        if s.country and s.country.isdigit():
            country = session.query(Country).get(int(s.country))
            if country:
                s.country = country.name
        # Исправить город
        if s.city and s.city.isdigit():
            city = session.query(City).get(int(s.city))
            if city:
                s.city = city.name
        # Исправить стадию
        if s.stage and s.stage.isdigit():
            stage = session.query(CompanyStage).get(int(s.stage))
            if stage:
                s.stage = stage.name
        # Исправить индустрию
        if s.industry and s.industry.isdigit():
            industry = session.query(Category).get(int(s.industry))
            if industry:
                s.industry = industry.name
    session.commit()
    session.close()

# --- Заполнение справочника стран ---
central_asia_countries = ["Казахстан", "Узбекистан", "Кыргызстан", "Таджикистан", "Туркменистан"]
if not session.query(Country).first():
    for name in central_asia_countries:
        session.add(Country(name=name, status="active"))
    session.commit()

if __name__ == "__main__":
    fix_company_fields()

session.close()
print('Таблицы созданы и тестовые данные добавлены (если база была пуста)!') 