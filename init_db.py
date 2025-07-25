from db import Base, engine, SessionLocal
import models
from models import *
from datetime import date, datetime, timedelta
from sqlalchemy import func

# Создать все таблицы
Base.metadata.create_all(bind=engine)

# Заполнить тестовыми данными, если база пуста
session = SessionLocal()
real_companies = [
    {
        "name": "CerebraAI",
        "description": "AI для диагностики инсульта и других заболеваний по КТ/МРТ. Лидер в HealthTech Казахстана.",
        "country": "Казахстан",
        "city": "Алматы",
        "stage": "Growth",
        "industry": "HealthTech",
        "website": "https://cerebraai.ai"
    },
    {
        "name": "Clockster",
        "description": "HRTech-платформа для учета рабочего времени и автоматизации HR-процессов.",
        "country": "Казахстан",
        "city": "Алматы",
        "stage": "Scale",
        "industry": "HRTech",
        "website": "https://clockster.com"
    },
    {
        "name": "ChocoFamily",
        "description": "Крупнейшая экосистема сервисов: доставка, финтех, маркетплейсы.",
        "country": "Казахстан",
        "city": "Алматы",
        "stage": "Growth",
        "industry": "E-commerce",
        "website": "https://chocofamily.kz"
    },
    {
        "name": "Documentolog",
        "description": "Электронный документооборот для бизнеса и госорганов.",
        "country": "Казахстан",
        "city": "Астана",
        "stage": "Scale",
        "industry": "SaaS",
        "website": "https://documentolog.kz"
    },
    {
        "name": "Alem School",
        "description": "IT-школа нового поколения для обучения программистов.",
        "country": "Казахстан",
        "city": "Алматы",
        "stage": "Growth",
        "industry": "EdTech",
        "website": "https://alem.school"
    },
    {
        "name": "MyTaxi",
        "description": "Сервис заказа такси в Узбекистане.",
        "country": "Узбекистан",
        "city": "Ташкент",
        "stage": "Growth",
        "industry": "Mobility",
        "website": "https://mytaxi.uz"
    },
    {
        "name": "Express24",
        "description": "Доставка еды и товаров в Узбекистане.",
        "country": "Узбекистан",
        "city": "Ташкент",
        "stage": "Growth",
        "industry": "Delivery",
        "website": "https://express24.uz"
    },
    {
        "name": "Billz",
        "description": "Облачная касса и автоматизация ритейла.",
        "country": "Узбекистан",
        "city": "Ташкент",
        "stage": "Seed",
        "industry": "RetailTech",
        "website": "https://billz.uz"
    },
    {
        "name": "Oquda",
        "description": "EdTech-платформа для поиска зарубежных вузов и подачи заявок.",
        "country": "Узбекистан",
        "city": "Ташкент",
        "stage": "Seed",
        "industry": "EdTech",
        "website": "https://oquda.com"
    },
    {
        "name": "TezSum",
        "description": "Финтех: электронные кошельки и платежи.",
        "country": "Узбекистан",
        "city": "Ташкент",
        "stage": "Growth",
        "industry": "Fintech",
        "website": "https://tezsum.uz"
    },
    {
        "name": "Dostavista",
        "description": "Служба доставки для бизнеса и частных лиц.",
        "country": "Казахстан",
        "city": "Алматы",
        "stage": "Growth",
        "industry": "Delivery",
        "website": "https://dostavista.kz"
    },
    {
        "name": "Tumar",
        "description": "Финтех и мобильные платежи в Кыргызстане.",
        "country": "Кыргызстан",
        "city": "Бишкек",
        "stage": "Seed",
        "industry": "Fintech",
        "website": "https://tumar.vc"
    },
    {
        "name": "SalamPay",
        "description": "Финтех-сервис для онлайн-платежей в Таджикистане.",
        "country": "Таджикистан",
        "city": "Душанбе",
        "stage": "Seed",
        "industry": "Fintech",
        "website": "https://salampay.tj"
    },
    {
        "name": "M-Doc",
        "description": "Телемедицина и онлайн-консультации врачей.",
        "country": "Казахстан",
        "city": "Алматы",
        "stage": "Seed",
        "industry": "HealthTech",
        "website": "https://mdoc.kz"
    },
    {
        "name": "SmartPay",
        "description": "Финтех-платформа для платежей и переводов.",
        "country": "Казахстан",
        "city": "Астана",
        "stage": "Growth",
        "industry": "Fintech",
        "website": "https://smartpay.kz"
    }
]

real_funds = [
    {
        "name": "MOST Ventures",
        "description": "Венчурный фонд, поддерживающий стартапы Центральной Евразии.",
        "country": "Казахстан",
        "focus": "Tech, SaaS, AI",
        "stages": "Seed, Series A",
        "website": "https://mostfund.vc",
        "type": "venture"
    },
    {
        "name": "Big Sky Capital",
        "description": "Фонд, инвестирующий в технологические компании региона.",
        "country": "Казахстан",
        "focus": "Tech, SaaS, AI",
        "stages": "Seed, Series A",
        "website": "https://bigskycapital.kz",
        "type": "venture"
    },
    {
        "name": "Quest Ventures",
        "description": "Один из крупнейших фондов Центральной Азии и Сингапура.",
        "country": "Казахстан",
        "focus": "AI, Fintech, SaaS",
        "stages": "Seed, Series A",
        "website": "https://www.questventures.com",
        "type": "venture"
    },
    {
        "name": "Tumar Venture Fund",
        "description": "Фонд из Кыргызстана, инвестирующий в стартапы региона.",
        "country": "Кыргызстан",
        "focus": "Fintech, SaaS",
        "stages": "Seed, Series A",
        "website": "https://tumar.vc",
        "type": "venture"
    },
    {
        "name": "UMAY Angels Club",
        "description": "Ангельский клуб для инвесторов и стартапов Центральной Азии.",
        "country": "Казахстан",
        "focus": "Tech, SaaS, AI",
        "stages": "Pre-seed, Seed",
        "website": "https://umay.vc",
        "type": "angel"
    },
    {
        "name": "QazAngels",
        "description": "Казахстанский клуб бизнес-ангелов.",
        "country": "Казахстан",
        "focus": "Tech, SaaS, AI",
        "stages": "Pre-seed, Seed",
        "website": "https://qazangels.com",
        "type": "angel"
    },
    {
        "name": "White Hill Capital",
        "description": "Венчурный фонд, инвестирующий в стартапы Казахстана.",
        "country": "Казахстан",
        "focus": "Tech, SaaS, AI",
        "stages": "Seed, Series A",
        "website": "https://whitehillcapital.com",
        "type": "venture"
    },
    {
        "name": "Astana Hub Ventures",
        "description": "Фонд при Astana Hub для поддержки стартапов.",
        "country": "Казахстан",
        "focus": "Tech, SaaS, AI",
        "stages": "Seed, Series A",
        "website": "https://astanahub.com",
        "type": "venture"
    },
    {
        "name": "AloqaVentures",
        "description": "Венчурный фонд из Узбекистана.",
        "country": "Узбекистан",
        "focus": "Fintech, SaaS, AI",
        "stages": "Seed, Series A",
        "website": "https://aloqaventures.com",
        "type": "venture"
    },
    {
        "name": "Sturgeon Capital",
        "description": "Международный фонд, инвестирующий в стартапы Узбекистана и региона.",
        "country": "Узбекистан",
        "focus": "Tech, SaaS, AI",
        "stages": "Seed, Series A",
        "website": "https://sturgeoncapital.com",
        "type": "venture"
    },
    {
        "name": "CentrAsia Angels",
        "description": "Региональный клуб бизнес-ангелов Центральной Азии.",
        "country": "Казахстан",
        "focus": "Tech, SaaS, AI",
        "stages": "Pre-seed, Seed",
        "website": "https://centrasiaangels.com",
        "type": "angel"
    }
]

# Оставляем только стартапы и фонды из Центральной Азии
central_asia_countries = ["Казахстан", "Узбекистан", "Кыргызстан", "Таджикистан", "Туркменистан"]
real_companies = [s for s in real_companies if s["country"] in central_asia_countries]
real_funds = [f for f in real_funds if f["country"] in central_asia_countries]

# --- Заполнение реальными стартапами ---
company_objs = []
investor_objs = []
if not session.query(Company).first():
    for s in real_companies:
        company = Company(
            name=s["name"],
            description=s["description"],
            country=s["country"],
            city=s["city"],
            stage=s["stage"],
            industry=s["industry"],
            founded_date=date(2021, 1, 1),
            website=s["website"]
        )
        session.add(company)
        company_objs.append(company)
    session.commit()

# --- Заполнение реальными фондами ---
if not session.query(Investor).first():
    for f in real_funds:
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
        investor_objs.append(investor)
    session.commit()

# --- Добавляем или обновляем команды, раунды и портфели для части стартапов и инвесторов ---
company_objs = session.query(Company).order_by(Company.id).all()
investor_objs = session.query(Investor).order_by(Investor.id).all()
if company_objs and investor_objs:
    # Команды для первых 5 стартапов
    team_names = [
        ["Айдар Ахметов", "CEO"],
        ["Мария Иванова", "CTO"],
        ["Данияр Ермеков", "COO"],
        ["Светлана Петрова", "CMO"],
        ["Азамат Садыков", "Product Manager"]
    ]
    for i, company in enumerate(company_objs[:5]):
        # Добавлять только если у стартапа нет команды
        if not company.team:
            for j in range(3):
                p = Person(name=team_names[(i+j)%5][0], role=team_names[(i+j)%5][1], country=company.country)
                session.add(p)
                company.team.append(p)
    session.commit()
    # Инвестиционные раунды для первых 3 стартапов
    for i, company in enumerate(company_objs[:3]):
        # Добавлять только если у стартапа нет раундов
        if not company.deals:
            deal = Deal(
                type="Seed",
                amount=500000 + i*250000,
                valuation=2000000 + i*500000,
                date=date(2022, 6, 1+i),
                currency="USD",
                investors=investor_objs[i % len(investor_objs)].name,
                status="active",
                company_id=company.id
            )
            session.add(deal)
            # Добавлять в портфель инвестора только если его там нет
            if company not in investor_objs[i % len(investor_objs)].portfolio:
                investor_objs[i % len(investor_objs)].portfolio.append(company)
    session.commit()

if not session.query(News).first():
    news_titles = [
        'Стартап FinSight привлек $1 млн инвестиций', 'Astana Ventures запускает новый фонд',
        'PayFlow выходит на рынок Узбекистана', 'HealthBridge внедряет AI в медицину',
        'AgroNext расширяет команду', 'Steppe Capital инвестирует в EdTech',
        'UrbanAI открывает офис в Бишкеке', 'Cloudify запускает облачный сервис',
        'HRBoost внедряет новые HR-технологии', 'LegalMind запускает платформу для юристов'
    ]
    for i, title in enumerate(news_titles):
        author = session.query(Author).order_by(func.random()).first()
        session.add(News(
            title=title,
            summary=f'Краткое описание: {title}',
            date=date.today() - timedelta(days=i),
            content=f'Полная статья: {title} — подробности и аналитика.',
            author_id=author.id if author else None,
            status='active'
        ))
    session.commit()

if not session.query(Podcast).first():
    podcast_titles = [
        'Инвестиции в Центральной Азии', 'Тренды Fintech 2024', 'Как строить EdTech-стартап',
        'AI в реальном бизнесе', 'Истории успеха: AgroNext', 'Женщины в IT',
        'Венчурные фонды региона', 'Будущее HRTech', 'Юридические стартапы',
        'Экология и технологии', 'Медицинские инновации'
    ]
    for i, title in enumerate(podcast_titles):
        session.add(Podcast(
            title=title,
            description=f'{title} — обсуждаем тренды и кейсы.',
            youtube_url='https://www.youtube.com/embed/dQw4w9WgXcQ',
            date=date.today() - timedelta(days=i*2),
            status='active'
        ))
    session.commit()

if not session.query(Event).first():
    event_titles = [
        'Startup Battle Astana', 'Tech Meetup Tashkent', 'Invest Day Almaty',
        'AI Conference Bishkek', 'Agro Forum Samarkand', 'Fintech Summit Nur-Sultan',
        'EdTech Expo', 'HealthTech Days', 'Logistics Innovation', 'HRTech Forum', 'LegalTech Meetup'
    ]
    for i, title in enumerate(event_titles):
        city = session.query(City).order_by(func.random()).first()
        session.add(Event(
            title=title,
            description=f'{title} — встреча профессионалов и экспертов.',
            date=datetime.now() + timedelta(days=i),
            format='Онлайн' if i % 2 == 0 else 'Оффлайн',
            location=city.name if city else 'Алматы',
            registration_url=f'https://event{i+1}.com',
            status='active'
        ))
    session.commit()

# --- Добавление тестовых пользователей-админов ---
kz = session.query(Country).filter_by(name="Казахстан").first()
kz_id = kz.id if kz else 1
if not session.query(User).filter_by(email="admin@stanbase.test").first():
    admin_user = User(
        email="admin@stanbase.test",
        password="admin123",  # для теста, в проде обязательно хешировать!
        role="admin",
        first_name="Admin",
        last_name="StanBase",
        country_id=1,
        city="Алматы",
        phone="+77001234567",
        status="active"
    )
    session.add(admin_user)
    session.commit()
if not session.query(User).filter_by(email="moderator@stanbase.test").first():
    moderator_user = User(
        email="moderator@stanbase.test",
        password="mod123",
        role="moderator",
        first_name="Mod",
        last_name="StanBase",
        country_id=1,
        city="Алматы",
        phone="+77001234568",
        status="active"
    )
    session.add(moderator_user)
    session.commit()
# --- Добавление тестового пользователя-стартапера ---
if not session.query(User).filter_by(email="company_owner@stanbase.test").first():
    company = session.query(Company).first()
    if company:
        company_owner_user = User(
            email="company_owner@stanbase.test",
            password="company_owner123",
            role="company_owner",
            first_name="Start",
            last_name="StanBase",
            country_id=kz_id,
            city="Алматы",
            phone="+77001234569",
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