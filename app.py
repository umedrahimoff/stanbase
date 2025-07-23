from flask import Flask, render_template, request, session, redirect, url_for, flash, abort, jsonify
from db import db
import os
from datetime import date, datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stanbase_secret_2024'  # Можно любой другой, но не пустой!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stanbase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Маршруты для SEO файлов
@app.route('/robots.txt')
def robots_txt():
    return app.send_static_file('robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return app.send_static_file('sitemap.xml')

def seed_data():
    from models import db, Country, City, StartupStage, Category, Startup, Investor, Person, Deal, Job, News, Podcast, Event, User, Author
    import random
    print('Добавляю тестовые справочники...')
    # Справочники
    countries = ['Казахстан', 'Узбекистан', 'Кыргызстан', 'Таджикистан', 'Туркменистан', 'Россия', 'США', 'Германия', 'Франция', 'Китай']
    country_objs = []
    for name in countries:
        c = Country(name=name, status='active')
        db.session.add(c)
        country_objs.append(c)
    db.session.commit()
    cities = [
        ('Алматы', 'Казахстан'), ('Астана', 'Казахстан'), ('Ташкент', 'Узбекистан'), ('Бишкек', 'Кыргызстан'),
        ('Душанбе', 'Таджикистан'), ('Ашхабад', 'Туркменистан'), ('Москва', 'Россия'), ('Нью-Йорк', 'США'),
        ('Берлин', 'Германия'), ('Париж', 'Франция'), ('Пекин', 'Китай')
    ]
    for name, country_name in cities:
        country = Country.query.filter_by(name=country_name).first()
        if country:
            db.session.add(City(name=name, country_id=country.id, status='active'))
    db.session.commit()
    stages = ['Idea', 'MVP', 'Seed', 'Series A', 'Series B', 'Growth', 'Exit']
    for name in stages:
        db.session.add(StartupStage(name=name, status='active'))
    db.session.commit()
    categories = ['Fintech', 'AI', 'Edtech', 'Healthtech', 'Agrotech', 'E-commerce', 'Travel', 'Logistics', 'HR', 'Legaltech']
    for name in categories:
        db.session.add(Category(name=name, status='active'))
    db.session.commit()
    print('Справочники заполнены!')
    # Авторы (издания)
    authors = [
        {'name': 'The Tech', 'description': 'Технологическое издание', 'website': 'https://thetech.uz', 'status': 'active'},
        {'name': 'Digital Business', 'description': 'Бизнес и диджитал', 'website': 'https://digitalbusiness.uz', 'status': 'active'},
        {'name': 'Spot.uz', 'description': 'Новости IT и бизнеса', 'website': 'https://www.spot.uz', 'status': 'active'},
        {'name': 'Pivot.uz', 'description': 'Стартапы и инновации', 'website': 'https://pivot.uz', 'status': 'active'},
        {'name': 'Startup Media', 'description': 'Медиа о стартапах', 'website': 'https://startupmedia.uz', 'status': 'active'},
        {'name': 'IT Review', 'description': 'Обзоры IT-рынка', 'website': 'https://itreview.uz', 'status': 'active'},
    ]
    author_objs = []
    for a in authors:
        author = Author(**a)
        db.session.add(author)
        author_objs.append(author)
    db.session.commit()
    # Реалистичные данные
    startup_names = [
        'FinSight', 'EduPro', 'HealthBridge', 'AgroNext', 'PayFlow', 'UrbanAI', 'Cloudify', 'Travelio', 'Logistix', 'HRBoost',
        'LegalMind', 'GreenTech', 'MedVision', 'SmartHome', 'FoodChain', 'DataGuard', 'SkillUp', 'BioGen', 'Marketly', 'Eventix'
    ]
    investor_names = [
        'Astana Ventures', 'Steppe Capital', 'Silk Road Angels', 'Eurasia Investments', 'Nomad Partners',
        'Alatau Capital', 'Turan Fund', 'Central Asia Growth', 'Samruk Invest', 'Infinity Capital',
        'NextGen Ventures', 'Pioneer Angels', 'Impact Fund', 'Visionary Capital', 'Altai Investments'
    ]
    person_names = [
        'Айдар Ахметов', 'Мария Иванова', 'Данияр Ермеков', 'Светлана Петрова', 'Азамат Садыков',
        'Елена Ким', 'Тимур Алиев', 'Гульнара Абдуллаева', 'Илья Смирнов', 'Жанна Турсунова',
        'Алексей Попов', 'Мадина Рахимова', 'Руслан Каримов', 'Виктория Ли', 'Бахтияр Исмаилов',
        'Алина Кузнецова', 'Ерлан Сулейменов', 'Саида Мухамедова', 'Павел Ким', 'Жанат Абдрахманов',
        'Динара Баймуханова', 'Арман Жумабеков', 'Сергей Ковалев', 'Гаухар Мусаева', 'Марат Абдуллин',
        'Кристина Юн', 'Азамат Тлеулин', 'Гульнар Садыкова', 'Игорь Ким', 'Салтанат Ахметова'
    ]
    job_titles = [
        'Backend Developer', 'Frontend Developer', 'Data Scientist', 'Product Manager', 'UI/UX Designer',
        'QA Engineer', 'DevOps Engineer', 'Mobile Developer', 'Business Analyst', 'Marketing Specialist'
    ]
    news_titles = [
        'Стартап FinSight привлек $1 млн инвестиций', 'Astana Ventures запускает новый фонд',
        'PayFlow выходит на рынок Узбекистана', 'HealthBridge внедряет AI в медицину',
        'AgroNext расширяет команду', 'Steppe Capital инвестирует в EdTech',
        'UrbanAI открывает офис в Бишкеке', 'Cloudify запускает облачный сервис',
        'HRBoost внедряет новые HR-технологии', 'LegalMind запускает платформу для юристов',
        'GreenTech получил грант на развитие', 'MedVision сотрудничает с клиниками',
        'SmartHome интегрируется с IoT', 'FoodChain выходит на рынок Казахстана'
    ]
    podcast_titles = [
        'Инвестиции в Центральной Азии', 'Тренды Fintech 2024', 'Как строить EdTech-стартап',
        'AI в реальном бизнесе', 'Истории успеха: AgroNext', 'Женщины в IT',
        'Венчурные фонды региона', 'Будущее HRTech', 'Юридические стартапы',
        'Экология и технологии', 'Медицинские инновации'
    ]
    event_titles = [
        'Startup Battle Astana', 'Tech Meetup Tashkent', 'Invest Day Almaty',
        'AI Conference Bishkek', 'Agro Forum Samarkand', 'Fintech Summit Nur-Sultan',
        'EdTech Expo', 'HealthTech Days', 'Logistics Innovation', 'HRTech Forum', 'LegalTech Meetup'
    ]
    # Пользователи
    usernames = [
        'admin', 'moderator', 'investor1', 'investor2', 'startuper1', 'startuper2',
        'user_aydar', 'user_maria', 'user_daniyar', 'user_svetlana', 'user_azamat',
        'user_elena', 'user_timur', 'user_gulnara', 'user_ilya', 'user_zhanna'
    ]
    for i, username in enumerate(usernames):
        db.session.add(User(username=username, password='test', role=random.choice(['admin','moderator','investor','startuper']), status='active'))
    db.session.commit()
    # Стартапы
    for i, name in enumerate(startup_names):
        country = random.choice(Country.query.all())
        city = random.choice(City.query.filter_by(country_id=country.id).all())
        stage = random.choice(StartupStage.query.all())
        category = random.choice(Category.query.all())
        s = Startup(
            name=name,
            description=f'{name} — инновационный проект в сфере {category.name}.',
            country=country.name,
            city=city.name,
            stage=stage.name,
            industry=category.name,
            founded_date=date(2020+i%3, (i%12)+1, (i%28)+1),
            website=f'https://{name.lower().replace(" ", "")}.com'
        )
        db.session.add(s)
    db.session.commit()
    # Инвесторы
    for i, name in enumerate(investor_names):
        country = random.choice(Country.query.all())
        focus = random.choice(categories)
        stage = random.choice(stages)
        db.session.add(Investor(
            name=name,
            description=f'{name} — ведущий инвестор.',
            country=country.name,
            focus=focus,
            stages=stage,
            website=f'https://{name.lower().replace(" ", "")}.com'
        ))
    db.session.commit()
    # Команда
    for i, name in enumerate(person_names):
        db.session.add(Person(
            name=name,
            country=random.choice(countries),
            linkedin=f'https://linkedin.com/in/{name.lower().replace(" ", "")}',
            role=random.choice(['CEO','CTO','COO','CMO','Developer','Designer'])
        ))
    db.session.commit()
    # Раунды (deals)
    for i in range(1, 20):
        s = random.choice(Startup.query.all())
        db.session.add(Deal(
            type=random.choice(stages),
            amount=random.randint(10000, 1000000),
            valuation=random.randint(100000, 5000000),
            date=date(2022, random.randint(1,12), random.randint(1,28)),
            currency='USD',
            startup_id=s.id,
            investors=random.choice(investor_names)
        ))
    db.session.commit()
    # Вакансии
    for i in range(1, 20):
        s = random.choice(Startup.query.all())
        city = random.choice(City.query.all())
        db.session.add(Job(
            title=random.choice(job_titles),
            description=f'Вакансия: {i} в {s.name}.',
            startup_id=s.id,
            city=city.name,
            job_type=random.choice(['Удалёнка','Полный день']),
            contact=f'hr@{s.name.lower().replace(" ", "")}.com'
        ))
    db.session.commit()
    # Новости
    for i, title in enumerate(news_titles):
        author = random.choice(author_objs)
        db.session.add(News(
            title=title,
            summary=f'Краткое описание: {title}',
            date=date.today() - timedelta(days=i),
            content=f'Полная статья: {title} — подробности и аналитика.',
            author_id=author.id
        ))
    db.session.commit()
    # Подкасты
    for i, title in enumerate(podcast_titles):
        db.session.add(Podcast(
            title=title,
            description=f'{title} — обсуждаем тренды и кейсы.',
            youtube_url='https://www.youtube.com/embed/dQw4w9WgXcQ',
            date=date.today() - timedelta(days=i*2)
        ))
    db.session.commit()
    # Мероприятия
    for i, title in enumerate(event_titles):
        city = random.choice(City.query.all())
        db.session.add(Event(
            title=title,
            description=f'{title} — встреча профессионалов и экспертов.',
            date=datetime.now() + timedelta(days=i),
            format=random.choice(['Онлайн','Оффлайн']),
            location=city.name,
            registration_url=f'https://event{i+1}.com'
        ))
    db.session.commit()
    print('Тестовые данные добавлены!')
    # Добавляем венчурные фонды с командой и портфелем
    venture_funds = [
        {'name': 'Steppe Ventures', 'description': 'Венчурный фонд Центральной Азии', 'country': 'Казахстан', 'focus': 'Fintech', 'stages': 'Seed, Series A', 'website': 'https://steppe.vc', 'type': 'venture'},
        {'name': 'Eurasia Capital', 'description': 'Фонд для стартапов региона', 'country': 'Узбекистан', 'focus': 'AI, Edtech', 'stages': 'MVP, Seed', 'website': 'https://eurasiacap.uz', 'type': 'venture'}
    ]
    for fund in venture_funds:
        inv = Investor(**fund)
        db.session.add(inv)
        db.session.commit()
        # Добавляем команду
        team = [
            Person(name='Алексей Фондов', country=fund['country'], linkedin='https://linkedin.com/in/alexfund', role='Managing Partner'),
            Person(name='Мария Стартапова', country=fund['country'], linkedin='https://linkedin.com/in/mariastartup', role='Investment Director')
        ]
        for p in team:
            db.session.add(p)
            db.session.commit()
            inv.team.append(p)
        db.session.commit()
        # Для Steppe Ventures — портфель из 3-5 стартапов
        if fund['name'] == 'Steppe Ventures':
            startups = Startup.query.order_by(db.func.random()).limit(5).all()
            for s in startups:
                inv.portfolio.append(s)
            db.session.commit()

def migrate_reference_data():
    from models import Startup, Country, City, StartupStage, Category, db
    # Страны
    countries = set([s.country for s in Startup.query if s.country])
    for name in countries:
        if not Country.query.filter_by(name=name).first():
            db.session.add(Country(name=name))
    db.session.commit()
    # Города
    for s in Startup.query:
        if s.city and s.country:
            country = Country.query.filter_by(name=s.country).first()
            if country and not City.query.filter_by(name=s.city, country_id=country.id).first():
                db.session.add(City(name=s.city, country_id=country.id))
    db.session.commit()
    # Стадии
    stages = set([s.stage for s in Startup.query if s.stage])
    for name in stages:
        if not StartupStage.query.filter_by(name=name).first():
            db.session.add(StartupStage(name=name))
    db.session.commit()
    # Категории (по industry)
    categories = set([s.industry for s in Startup.query if s.industry])
    for name in categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()

def init_test_users():
    """Создает тестовых пользователей, если их еще нет"""
    # Список тестовых пользователей
    test_users = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
        {'username': 'superadmin', 'password': 'super123', 'role': 'admin'},
        {'username': 'moderator1', 'password': 'mod123', 'role': 'moderator'},
        {'username': 'investor1', 'password': 'inv123', 'role': 'investor'},
        {'username': 'startuper1', 'password': 'start123', 'role': 'startuper'},
    ]
    
    created_count = 0
    for user_data in test_users:
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user:
            user = User(
                username=user_data['username'],
                password=user_data['password'],
                role=user_data['role'],
                status='active'
            )
            db.session.add(user)
            created_count += 1
            print(f"✅ Создан пользователь: {user_data['username']} (роль: {user_data['role']})")
        else:
            # Обновляем пароль и роль, если пользователь уже существует
            existing_user.password = user_data['password']
            existing_user.role = user_data['role']
            print(f"🔄 Обновлен пользователь: {user_data['username']} (роль: {user_data['role']})")
    
    if created_count > 0:
        db.session.commit()
        print(f"\n📊 Создано новых пользователей: {created_count}")
    
    print("\n📋 Доступные тестовые пользователи:")
    print("=" * 50)
    print("Администраторы:")
    print("  Логин: admin, Пароль: admin123")
    print("  Логин: superadmin, Пароль: super123")
    print("\nМодераторы:")
    print("  Логин: moderator1, Пароль: mod123")
    print("\nИнвесторы:")
    print("  Логин: investor1, Пароль: inv123")
    print("\nСтартаперы:")
    print("  Логин: startuper1, Пароль: start123")

with app.app_context():
    from models import Startup, Investor, Person, Deal, Job, News, Podcast, Event, User
    db.create_all()
    # Добавляем тестовые данные всегда в новую базу
    if not Startup.query.first():
        seed_data()
    
    # Инициализируем тестовых пользователей
    init_test_users()


@app.route('/')
def index():
    from models import Startup, Investor, News, Podcast, Job, Event, Deal
    startups = Startup.query.order_by(Startup.id.desc()).limit(20).all()
    investors = Investor.query.order_by(Investor.id.desc()).limit(20).all()
    news = News.query.order_by(News.date.desc()).limit(10).all()
    podcasts = Podcast.query.order_by(Podcast.date.desc()).limit(10).all()
    jobs = Job.query.order_by(Job.id.desc()).limit(10).all()
    events = Event.query.order_by(Event.date.desc()).limit(10).all()
    # Аналитика только по странам ЦА (оставляю на случай будущего виджета)
    ca_countries = ['Казахстан', 'Узбекистан', 'Кыргызстан', 'Таджикистан', 'Туркменистан']
    deals = Deal.query.filter(Deal.date != None).all()
    analytics = []
    for d in deals:
        if d.startup and d.date and d.startup.country in ca_countries:
            analytics.append({'country': d.startup.country, 'amount': d.amount or 0, 'year': d.date.year})
    years = [row['year'] for row in analytics]
    last_year = max(years) if years else None
    by_country = {c: 0 for c in ca_countries}
    if last_year:
        for row in analytics:
            if row['year'] == last_year:
                by_country[row['country']] += row['amount']
    labels = ca_countries
    values = [by_country[c] for c in ca_countries]
    return render_template('index.html', startups=startups, investors=investors, news=news, podcasts=podcasts, jobs=jobs, events=events)

@app.route('/startups')
def startups():
    q = request.args.get('q', '').strip()
    country = request.args.get('country', '')
    stage = request.args.get('stage', '')
    industry = request.args.get('industry', '')

    query = Startup.query
    if q:
        query = query.filter(Startup.name.ilike(f'%{q}%'))
    if country:
        query = query.filter_by(country=country)
    if stage:
        query = query.filter_by(stage=stage)
    if industry:
        query = query.filter_by(industry=industry)
    startups = query.order_by(Startup.name).all()

    # Для фильтров — уникальные значения
    countries = [c[0] for c in db.session.query(Startup.country).distinct().order_by(Startup.country) if c[0]]
    stages = [s[0] for s in db.session.query(Startup.stage).distinct().order_by(Startup.stage) if s[0]]
    industries = [i[0] for i in db.session.query(Startup.industry).distinct().order_by(Startup.industry) if i[0]]

    return render_template('public/startups/list.html', startups=startups, countries=countries, stages=stages, industries=industries)

@app.route('/startup/<int:id>')
def startup_profile(id):
    from models import Startup, Investor
    startup = Startup.query.get_or_404(id)
    # Похожие стартапы по индустрии, кроме текущего
    similar = Startup.query.filter(Startup.industry == startup.industry, Startup.id != startup.id).order_by(Startup.id.desc()).limit(4).all()
    all_investors = Investor.query.all()
    investor_dict = {inv.name: inv for inv in all_investors}
    return render_template('public/startups/detail.html', startup=startup, similar=similar, investor_dict=investor_dict)

@app.route('/investors')
def investors():
    q = request.args.get('q', '').strip()
    country = request.args.get('country', '')
    focus = request.args.get('focus', '').strip()
    stages = request.args.get('stages', '').strip()

    query = Investor.query
    if q:
        query = query.filter(Investor.name.ilike(f'%{q}%'))
    if country:
        query = query.filter_by(country=country)
    if focus:
        query = query.filter(Investor.focus.ilike(f'%{focus}%'))
    if stages:
        query = query.filter(Investor.stages.ilike(f'%{stages}%'))
    investors = query.order_by(Investor.name).all()

    countries = [c[0] for c in db.session.query(Investor.country).distinct().order_by(Investor.country) if c[0]]

    return render_template('public/investors/list.html', investors=investors, countries=countries)

@app.route('/investor/<int:id>')
def investor_profile(id):
    from models import Investor
    investor = Investor.query.get_or_404(id)
    # Тип инвестора по полю type
    if hasattr(investor, 'type'):
        if investor.type == 'angel':
            inv_type = 'Ангельский инвестор'
        elif investor.type == 'venture':
            inv_type = 'Венчурный фонд'
        else:
            inv_type = 'Прочие инвестиции'
    else:
        # Fallback для старых данных
        name_lower = investor.name.lower()
        if 'angel' in name_lower or 'ангел' in name_lower:
            inv_type = 'Ангельский инвестор'
        elif 'venture' in name_lower or 'венчур' in name_lower or 'capital' in name_lower or 'фонд' in name_lower:
            inv_type = 'Венчурный фонд'
        else:
            inv_type = 'Прочие инвестиции'
    # Похожие инвесторы по фокусу или стране
    similar = Investor.query.filter(
        (Investor.focus == investor.focus) | (Investor.country == investor.country),
        Investor.id != investor.id
    ).order_by(Investor.id.desc()).limit(4).all()
    return render_template('public/investors/detail.html', investor=investor, inv_type=inv_type, similar=similar)

@app.route('/news')
def news_list():
    from models import News
    news = News.query.order_by(News.date.desc()).all()
    return render_template('public/news/list.html', news=news)

@app.route('/news/<int:id>')
def news_detail(id):
    from models import News
    n = News.query.get_or_404(id)
    return render_template('public/news/detail.html', news=n)

@app.route('/events')
def events_list():
    from models import Event
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('public/events/list.html', events=events)

@app.route('/event/<int:id>')
def event_detail(id):
    from models import Event
    e = Event.query.get_or_404(id)
    return render_template('public/events/detail.html', event=e)

@app.route('/jobs')
def jobs_list():
    from models import Job, Startup
    q = request.args.get('q', '').strip()
    city = request.args.get('city', '')
    job_type = request.args.get('job_type', '')
    startup_id = request.args.get('startup', '')
    query = Job.query
    if q:
        query = query.filter(Job.title.ilike(f'%{q}%'))
    if city:
        query = query.filter_by(city=city)
    if job_type:
        query = query.filter_by(job_type=job_type)
    if startup_id:
        query = query.filter_by(startup_id=startup_id)
    jobs = query.order_by(Job.id.desc()).all()
    # Для фильтров
    cities = [c[0] for c in db.session.query(Job.city).distinct().order_by(Job.city) if c[0]]
    job_types = [t[0] for t in db.session.query(Job.job_type).distinct().order_by(Job.job_type) if t[0]]
    startups = Startup.query.order_by(Startup.name).all()
    return render_template('public/jobs/list.html', jobs=jobs, cities=cities, job_types=job_types, startups=startups)

@app.route('/job/<int:id>')
def job_detail(id):
    from models import Job
    j = Job.query.get_or_404(id)
    return render_template('public/jobs/detail.html', job=j)

@app.route('/podcasts')
def podcasts_list():
    from models import Podcast
    podcasts = Podcast.query.order_by(Podcast.date.desc()).all()
    return render_template('public/podcasts/list.html', podcasts=podcasts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import User
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role in ['admin', 'moderator']:
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'investor':
                return redirect(url_for('dashboard_investor'))
            else:
                return redirect(url_for('dashboard_startuper'))
        else:
            error = 'Неверный логин или пароль'
    return render_template('auth/login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    from models import User, Investor, Startup
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            error = 'Пользователь с таким логином уже существует'
        else:
            if role == 'investor':
                investor = Investor(name=f'Инвестор {username}', description='', country='', focus='', stages='', website='')
                db.session.add(investor)
                db.session.commit()
                user = User(username=username, password=password, role=role, investor_id=investor.id)
            else:
                startup = Startup(name=f'Стартап {username}', description='', country='', city='', stage='', industry='', founded_date=None, website='')
                db.session.add(startup)
                db.session.commit()
                user = User(username=username, password=password, role=role, startup_id=startup.id)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь войдите.')
            return redirect(url_for('login'))
    return render_template('auth/register.html', error=error)

@app.route('/dashboard/investor')
def dashboard_investor():
    from models import User, Investor
    user = None
    investor = None
    if 'user_id' in session and session.get('role') == 'investor':
        user = User.query.get(session['user_id'])
        investor = Investor.query.get(user.investor_id)
    return render_template('dashboard/investor.html', user=user, investor=investor)

@app.route('/dashboard/startuper')
def dashboard_startuper():
    from models import User, Startup
    user = None
    startup = None
    if 'user_id' in session and session.get('role') == 'startuper':
        user = User.query.get(session['user_id'])
        startup = Startup.query.get(user.startup_id)
    return render_template('dashboard/startuper.html', user=user, startup=startup)

# --- Инвестор: редактирование профиля ---
@app.route('/dashboard/investor/edit', methods=['GET', 'POST'])
def edit_investor():
    from models import User, Investor
    if 'user_id' not in session or session.get('role') != 'investor':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    investor = Investor.query.get(user.investor_id)
    if not investor:
        abort(404)
    if request.method == 'POST':
        investor.name = request.form['name']
        investor.description = request.form['description']
        investor.country = request.form['country']
        investor.focus = request.form['focus']
        investor.stages = request.form['stages']
        investor.website = request.form['website']
        db.session.commit()
        flash('Профиль обновлён!')
        return redirect(url_for('dashboard_investor'))
    return render_template('edit_investor.html', investor=investor)

# --- Стартапер: редактирование профиля ---
@app.route('/dashboard/startuper/edit', methods=['GET', 'POST'])
def edit_startuper():
    from models import User, Startup
    if 'user_id' not in session or session.get('role') != 'startuper':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    startup = Startup.query.get(user.startup_id)
    if not startup:
        abort(404)
    if request.method == 'POST':
        startup.name = request.form['name']
        startup.description = request.form['description']
        startup.country = request.form['country']
        startup.city = request.form['city']
        startup.stage = request.form['stage']
        startup.industry = request.form['industry']
        startup.website = request.form['website']
        db.session.commit()
        flash('Профиль стартапа обновлён!')
        return redirect(url_for('dashboard_startuper'))
    return render_template('edit_startuper.html', startup=startup)

# --- Стартапер: добавление/удаление члена команды ---
@app.route('/dashboard/startuper/team/add', methods=['POST'])
def add_team_member():
    from models import User, Startup, Person
    if 'user_id' not in session or session.get('role') != 'startuper':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    startup = Startup.query.get(user.startup_id)
    if not startup:
        abort(404)
    name = request.form['name']
    role = request.form['role']
    linkedin = request.form['linkedin']
    person = Person(name=name, role=role, linkedin=linkedin, country=startup.country)
    db.session.add(person)
    db.session.commit()
    startup.team.append(person)
    db.session.commit()
    flash('Член команды добавлен!')
    return redirect(url_for('dashboard_startuper'))

@app.route('/dashboard/startuper/team/delete/<int:person_id>', methods=['POST'])
def delete_team_member(person_id):
    from models import User, Startup, Person
    if 'user_id' not in session or session.get('role') != 'startuper':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    startup = Startup.query.get(user.startup_id)
    person = Person.query.get(person_id)
    if not startup or not person or person not in startup.team:
        abort(404)
    startup.team.remove(person)
    db.session.commit()
    flash('Член команды удалён!')
    return redirect(url_for('dashboard_startuper'))

# --- Инвестор: добавление/удаление стартапа в портфель ---
@app.route('/dashboard/investor/portfolio/add', methods=['POST'])
def add_portfolio():
    from models import User, Investor, Startup
    if 'user_id' not in session or session.get('role') != 'investor':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    investor = Investor.query.get(user.investor_id)
    startup_id = int(request.form['startup_id'])
    startup = Startup.query.get(startup_id)
    if startup and startup not in investor.portfolio:
        investor.portfolio.append(startup)
        db.session.commit()
        flash('Стартап добавлен в портфель!')
    return redirect(url_for('dashboard_investor'))

@app.route('/dashboard/investor/portfolio/delete/<int:startup_id>', methods=['POST'])
def delete_portfolio(startup_id):
    from models import User, Investor, Startup
    if 'user_id' not in session or session.get('role') != 'investor':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    investor = Investor.query.get(user.investor_id)
    startup = Startup.query.get(startup_id)
    if startup and startup in investor.portfolio:
        investor.portfolio.remove(startup)
        db.session.commit()
        flash('Стартап удалён из портфеля!')
    return redirect(url_for('dashboard_investor'))

@app.route('/analytics')
def analytics():
    from models import Deal, Startup
    import datetime
    # Получаем все года, в которых были сделки
    years = sorted({d.date.year for d in Deal.query if d.date}, reverse=True)
    year = int(request.args.get('year', years[0] if years else datetime.date.today().year))
    # Считаем по странам
    stats = {}
    deals = Deal.query.filter(Deal.date != None).all()
    for d in deals:
        if d.date.year == year:
            country = d.startup.country if d.startup else 'Неизвестно'
            if country not in stats:
                stats[country] = {'sum': 0, 'count': 0}
            stats[country]['sum'] += d.amount or 0
            stats[country]['count'] += 1
    stats = sorted(stats.items(), key=lambda x: -x[1]['sum'])
    return render_template('public/analytics.html', stats=stats, years=years, year=year)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['admin', 'moderator']:
            flash('Доступ разрешён только администраторам и модераторам.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    from models import User, Investor, Startup, News, Event, Job, Deal
    users = User.query.all()
    investors = Investor.query.all()
    startups = Startup.query.all()
    news = News.query.all()
    events = Event.query.all()
    jobs = Job.query.all()
    deals = Deal.query.all()
    return render_template('admin/dashboard.html', users=users, investors=investors, startups=startups, news=news, events=events, jobs=jobs, deals=deals)

@app.route('/admin/users')
@admin_required
def admin_users():
    from models import User
    q = request.args.get('q', '').strip()
    per_page = int(request.args.get('per_page', 10))
    page = int(request.args.get('page', 1))
    status = request.args.get('status', '')
    query = User.query
    if q:
        query = query.filter(User.username.ilike(f'%{q}%'))
    if status:
        query = query.filter(User.status == status)
    total = query.count()
    users = query.order_by(User.id).offset((page-1)*per_page).limit(per_page).all()
    return render_template('admin/users/list.html', users=users, q=q, per_page=per_page, page=page, total=total)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@admin_required
def admin_create_user():
    from models import User
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        status = request.form['status']
        if User.query.filter_by(username=username).first():
            error = 'Пользователь с таким логином уже существует'
        else:
            user = User(username=username, password=password, role=role, status=status)
            db.session.add(user)
            db.session.commit()
            flash('Пользователь создан!')
            return redirect(url_for('admin_users'))
    return render_template('admin/users/form.html', error=error, user=None)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    from models import User
    user = User.query.get_or_404(user_id)
    error = None
    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:
            user.password = request.form['password']
        user.role = request.form['role']
        user.status = request.form['status']
        db.session.commit()
        flash('Пользователь обновлён!')
        return redirect(url_for('admin_users'))
    return render_template('admin/users/form.html', error=error, user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    from models import User
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удалён!')
    return redirect(url_for('admin_users'))

@app.route('/admin/startups')
@admin_required
def admin_startups():
    from models import Startup
    q = request.args.get('q', '').strip()
    per_page = int(request.args.get('per_page', 10))
    page = int(request.args.get('page', 1))
    query = Startup.query
    if q:
        query = query.filter(Startup.name.ilike(f'%{q}%'))
    total = query.count()
    startups = query.order_by(Startup.id).offset((page-1)*per_page).limit(per_page).all()
    return render_template('admin/startups/list.html', startups=startups, q=q, per_page=per_page, page=page, total=total)

@app.route('/admin/startups/create', methods=['GET', 'POST'])
@admin_required
def admin_create_startup():
    from models import Startup
    error = None
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        country = request.form['country']
        city = request.form['city']
        stage = request.form['stage']
        industry = request.form['industry']
        founded_date = request.form['founded_date'] or None
        website = request.form['website']
        startup = Startup(
            name=name,
            description=description,
            country=country,
            city=city,
            stage=stage,
            industry=industry,
            founded_date=founded_date,
            website=website
        )
        db.session.add(startup)
        db.session.commit()
        flash('Стартап создан!')
        return redirect(url_for('admin_startups'))
    return render_template('admin/startups/form.html', error=error, startup=None)

@app.route('/admin/startups/edit/<int:startup_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_startup(startup_id):
    from models import Startup
    startup = Startup.query.get_or_404(startup_id)
    error = None
    if request.method == 'POST':
        startup.name = request.form['name']
        startup.description = request.form['description']
        startup.country = request.form['country']
        startup.city = request.form['city']
        startup.stage = request.form['stage']
        startup.industry = request.form['industry']
        startup.founded_date = request.form['founded_date'] or None
        startup.website = request.form['website']
        db.session.commit()
        flash('Стартап обновлён!')
        return redirect(url_for('admin_startups'))
    # Передаю связанные объекты
    team = startup.team
    deals = startup.deals
    jobs = startup.jobs
    return render_template('admin/startups/form.html', error=error, startup=startup, team=team, deals=deals, jobs=jobs)

@app.route('/admin/startups/delete/<int:startup_id>', methods=['POST'])
@admin_required
def admin_delete_startup(startup_id):
    from models import Startup
    startup = Startup.query.get_or_404(startup_id)
    db.session.delete(startup)
    db.session.commit()
    flash('Стартап удалён!')
    return redirect(url_for('admin_startups'))

@app.route('/admin/investors')
@admin_required
def admin_investors():
    from models import Investor
    q = request.args.get('q', '').strip()
    per_page = int(request.args.get('per_page', 10))
    page = int(request.args.get('page', 1))
    query = Investor.query
    if q:
        query = query.filter(Investor.name.ilike(f'%{q}%'))
    total = query.count()
    investors = query.order_by(Investor.id).offset((page-1)*per_page).limit(per_page).all()
    return render_template('admin/investors/list.html', investors=investors, q=q, per_page=per_page, page=page, total=total)

@app.route('/admin/investors/create', methods=['GET', 'POST'])
@admin_required
def admin_create_investor():
    from models import Investor
    error = None
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        country = request.form['country']
        focus = request.form['focus']
        stages = request.form['stages']
        website = request.form['website']
        type_ = request.form['type']
        investor = Investor(
            name=name,
            description=description,
            country=country,
            focus=focus,
            stages=stages,
            website=website,
            type=type_
        )
        db.session.add(investor)
        db.session.commit()
        flash('Инвестор создан!')
        return redirect(url_for('admin_investors'))
    return render_template('admin/investors/form.html', error=error, investor=None)

@app.route('/admin/investors/edit/<int:investor_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_investor(investor_id):
    from models import Investor
    investor = Investor.query.get_or_404(investor_id)
    error = None
    if request.method == 'POST':
        investor.name = request.form['name']
        investor.description = request.form['description']
        investor.country = request.form['country']
        investor.focus = request.form['focus']
        investor.stages = request.form['stages']
        investor.website = request.form['website']
        investor.type = request.form['type']
        db.session.commit()
        flash('Инвестор обновлён!')
        return redirect(url_for('admin_investors'))
    return render_template('admin/investors/form.html', error=error, investor=investor, today=date.today())

@app.route('/admin/investors/delete/<int:investor_id>', methods=['POST'])
@admin_required
def admin_delete_investor(investor_id):
    from models import Investor
    investor = Investor.query.get_or_404(investor_id)
    db.session.delete(investor)
    db.session.commit()
    flash('Инвестор удалён!')
    return redirect(url_for('admin_investors'))

@app.route('/admin/news')
@admin_required
def admin_news():
    from models import News
    q = request.args.get('q', '').strip()
    per_page = int(request.args.get('per_page', 10))
    page = int(request.args.get('page', 1))
    query = News.query
    if q:
        query = query.filter(News.title.ilike(f'%{q}%'))
    total = query.count()
    news = query.order_by(News.date.desc()).offset((page-1)*per_page).limit(per_page).all()
    return render_template('admin/news/list.html', news=news, q=q, per_page=per_page, page=page, total=total)

@app.route('/admin/news/create', methods=['GET', 'POST'])
@admin_required
def admin_create_news():
    from models import News
    from datetime import date
    error = None
    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        content = request.form['content']
        news_date_str = request.form['date'] or str(date.today())
        from datetime import datetime
        news_date = datetime.strptime(news_date_str, '%Y-%m-%d').date() if news_date_str else None
        news_item = News(
            title=title,
            summary=summary,
            content=content,
            date=news_date
        )
        db.session.add(news_item)
        db.session.commit()
        flash('Новость создана!')
        return redirect(url_for('admin_news'))
    return render_template('admin/news/form.html', error=error, news_item=None)

@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_news(news_id):
    from models import News
    news_item = News.query.get_or_404(news_id)
    error = None
    if request.method == 'POST':
        news_item.title = request.form['title']
        news_item.summary = request.form['summary']
        news_item.content = request.form['content']
        news_date_str = request.form['date']
        from datetime import datetime
        news_item.date = datetime.strptime(news_date_str, '%Y-%m-%d').date() if news_date_str else None
        db.session.commit()
        flash('Новость обновлена!')
        return redirect(url_for('admin_news'))
    return render_template('admin/news/form.html', error=error, news_item=news_item)

@app.route('/admin/news/delete/<int:news_id>', methods=['POST'])
@admin_required
def admin_delete_news(news_id):
    from models import News
    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()
    flash('Новость удалена!')
    return redirect(url_for('admin_news'))

@app.route('/admin/countries', methods=['GET', 'POST'])
@admin_required
def admin_countries():
    from models import Country
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name and not Country.query.filter_by(name=name).first():
            db.session.add(Country(name=name))
            db.session.commit()
        else:
            error = 'Такая страна уже есть или имя пустое.'
    countries = Country.query.order_by(Country.name).all()
    return render_template('admin/countries/list.html', countries=countries, error=error)

@app.route('/admin/cities', methods=['GET', 'POST'])
@admin_required
def admin_cities():
    from models import City, Country
    error = None
    countries = Country.query.order_by(Country.name).all()
    if request.method == 'POST':
        name = request.form['name'].strip()
        country_id = request.form.get('country_id')
        if name and country_id and not City.query.filter_by(name=name, country_id=country_id).first():
            db.session.add(City(name=name, country_id=country_id))
            db.session.commit()
        else:
            error = 'Такой город уже есть или не выбрана страна.'
    cities = City.query.order_by(City.name).all()
    return render_template('admin/cities/list.html', cities=cities, countries=countries, error=error)

@app.route('/admin/stages', methods=['GET', 'POST'])
@admin_required
def admin_stages():
    from models import StartupStage
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name and not StartupStage.query.filter_by(name=name).first():
            db.session.add(StartupStage(name=name))
            db.session.commit()
        else:
            error = 'Такая стадия уже есть или имя пустое.'
    stages = StartupStage.query.order_by(StartupStage.name).all()
    return render_template('admin/stages/list.html', stages=stages, error=error)

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    from models import Category
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name and not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
            db.session.commit()
        else:
            error = 'Такая категория уже есть или имя пустое.'
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories/list.html', categories=categories, error=error)

@app.route('/admin/countries/edit/<int:country_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_country(country_id):
    from models import Country
    country = Country.query.get_or_404(country_id)
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name and not Country.query.filter_by(name=name).first():
            country.name = name
            db.session.commit()
            flash('Страна обновлена!')
            return redirect(url_for('admin_countries'))
        else:
            error = 'Такая страна уже есть или имя пустое.'
    return render_template('admin/countries/form.html', country=country, error=error)

@app.route('/admin/countries/delete/<int:country_id>', methods=['POST'])
@admin_required
def admin_delete_country(country_id):
    from models import Country
    country = Country.query.get_or_404(country_id)
    db.session.delete(country)
    db.session.commit()
    flash('Страна удалена!')
    return redirect(url_for('admin_countries'))

@app.route('/admin/cities/edit/<int:city_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_city(city_id):
    from models import City, Country
    city = City.query.get_or_404(city_id)
    countries = Country.query.order_by(Country.name).all()
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        country_id = request.form.get('country_id')
        if name and country_id and not City.query.filter_by(name=name, country_id=country_id).first():
            city.name = name
            city.country_id = country_id
            db.session.commit()
            flash('Город обновлён!')
            return redirect(url_for('admin_cities'))
        else:
            error = 'Такой город уже есть или не выбрана страна.'
    return render_template('admin/cities/form.html', city=city, countries=countries, error=error)

@app.route('/admin/cities/delete/<int:city_id>', methods=['POST'])
@admin_required
def admin_delete_city(city_id):
    from models import City
    city = City.query.get_or_404(city_id)
    db.session.delete(city)
    db.session.commit()
    flash('Город удалён!')
    return redirect(url_for('admin_cities'))

@app.route('/admin/stages/edit/<int:stage_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_stage(stage_id):
    from models import StartupStage
    stage = StartupStage.query.get_or_404(stage_id)
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name and not StartupStage.query.filter_by(name=name).first():
            stage.name = name
            db.session.commit()
            flash('Стадия обновлена!')
            return redirect(url_for('admin_stages'))
        else:
            error = 'Такая стадия уже есть или имя пустое.'
    return render_template('admin/stages/form.html', stage=stage, error=error)

@app.route('/admin/stages/delete/<int:stage_id>', methods=['POST'])
@admin_required
def admin_delete_stage(stage_id):
    from models import StartupStage
    stage = StartupStage.query.get_or_404(stage_id)
    db.session.delete(stage)
    db.session.commit()
    flash('Стадия удалена!')
    return redirect(url_for('admin_stages'))

@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(category_id):
    from models import Category
    category = Category.query.get_or_404(category_id)
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name and not Category.query.filter_by(name=name).first():
            category.name = name
            db.session.commit()
            flash('Категория обновлена!')
            return redirect(url_for('admin_categories'))
        else:
            error = 'Такая категория уже есть или имя пустое.'
    return render_template('admin/categories/form.html', category=category, error=error)

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    from models import Category
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Категория удалена!')
    return redirect(url_for('admin_categories'))

@app.route('/admin/jobs')
@admin_required
def admin_jobs():
    from models import Job, Startup
    q = request.args.get('q', '').strip()
    per_page = int(request.args.get('per_page', 10))
    page = int(request.args.get('page', 1))
    query = Job.query
    if q:
        query = query.filter(Job.title.ilike(f'%{q}%'))
    total = query.count()
    jobs = query.order_by(Job.id.desc()).offset((page-1)*per_page).limit(per_page).all()
    startups = {s.id: s for s in Startup.query.all()}
    return render_template('admin/jobs/list.html', jobs=jobs, q=q, per_page=per_page, page=page, total=total, startups=startups)

@app.route('/admin/jobs/create', methods=['GET', 'POST'])
@admin_required
def admin_create_job():
    from models import Job, Startup
    error = None
    startups = Startup.query.order_by(Startup.name).all()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        startup_id = request.form['startup_id'] or None
        city = request.form['city']
        job_type = request.form['job_type']
        contact = request.form['contact']
        job = Job(
            title=title,
            description=description,
            startup_id=startup_id,
            city=city,
            job_type=job_type,
            contact=contact
        )
        db.session.add(job)
        db.session.commit()
        flash('Вакансия создана!')
        return redirect(url_for('admin_jobs'))
    return render_template('admin/jobs/form.html', error=error, job=None, startups=startups)

@app.route('/admin/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_job(job_id):
    from models import Job, Startup
    job = Job.query.get_or_404(job_id)
    error = None
    startups = Startup.query.order_by(Startup.name).all()
    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.startup_id = request.form['startup_id'] or None
        job.city = request.form['city']
        job.job_type = request.form['job_type']
        job.contact = request.form['contact']
        db.session.commit()
        flash('Вакансия обновлена!')
        return redirect(url_for('admin_jobs'))
    return render_template('admin/jobs/form.html', error=error, job=job, startups=startups)

@app.route('/admin/jobs/delete/<int:job_id>', methods=['POST'])
@admin_required
def admin_delete_job(job_id):
    from models import Job
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Вакансия удалена!')
    return redirect(url_for('admin_jobs'))

@app.route('/admin/startup_search')
@admin_required
def admin_startup_search():
    from models import Startup
    q = request.args.get('q', '').strip()
    results = []
    if q and len(q) >= 2:
        startups = Startup.query.filter(Startup.name.ilike(f'%{q}%')).order_by(Startup.name).limit(20).all()
        results = [{'id': s.id, 'text': s.name} for s in startups]
    return jsonify({'results': results})

@app.route('/admin/startup_info/<int:startup_id>')
@admin_required
def admin_startup_info(startup_id):
    from models import Startup
    s = Startup.query.get_or_404(startup_id)
    return jsonify({
        'id': s.id,
        'name': s.name,
        'city': s.city,
        'country': s.country,
        'stage': s.stage,
        'industry': s.industry,
        'website': s.website
    })

@app.route('/admin/authors')
@admin_required
def admin_authors():
    from models import Author
    q = request.args.get('q', '').strip()
    per_page = int(request.args.get('per_page', 10))
    page = int(request.args.get('page', 1))
    query = Author.query
    if q:
        query = query.filter(Author.name.ilike(f'%{q}%'))
    total = query.count()
    authors = query.order_by(Author.id).offset((page-1)*per_page).limit(per_page).all()
    return render_template('admin/authors/list.html', authors=authors, q=q, per_page=per_page, page=page, total=total)

@app.route('/admin/authors/create', methods=['GET', 'POST'])
@admin_required
def admin_create_author():
    from models import Author
    error = None
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        website = request.form['website']
        status = request.form['status']
        author = Author(name=name, description=description, website=website, status=status)
        db.session.add(author)
        db.session.commit()
        flash('Автор создан!')
        return redirect(url_for('admin_authors'))
    return render_template('admin/authors/form.html', error=error, author=None)

@app.route('/admin/authors/edit/<int:author_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_author(author_id):
    from models import Author
    author = Author.query.get_or_404(author_id)
    error = None
    if request.method == 'POST':
        author.name = request.form['name']
        author.description = request.form['description']
        author.website = request.form['website']
        author.status = request.form['status']
        db.session.commit()
        flash('Автор обновлён!')
        return redirect(url_for('admin_authors'))
    return render_template('admin/authors/form.html', error=error, author=author)

@app.route('/admin/authors/delete/<int:author_id>', methods=['POST'])
@admin_required
def admin_delete_author(author_id):
    from models import Author
    author = Author.query.get_or_404(author_id)
    db.session.delete(author)
    db.session.commit()
    flash('Автор удалён!')
    return redirect(url_for('admin_authors'))

@app.route('/admin/investors/<int:investor_id>/portfolio/add', methods=['POST'])
@admin_required
def admin_add_portfolio_startup(investor_id):
    from models import Investor, Startup
    investor = Investor.query.get_or_404(investor_id)
    startup_id = int(request.form['startup_id'])
    startup = Startup.query.get_or_404(startup_id)
    if startup not in investor.portfolio:
        investor.portfolio.append(startup)
        db.session.commit()
        flash('Стартап добавлен в портфель!')
    return redirect(url_for('admin_edit_investor', investor_id=investor_id))

@app.route('/admin/investors/<int:investor_id>/portfolio/delete/<int:startup_id>', methods=['POST'])
@admin_required
def admin_delete_portfolio_startup(investor_id, startup_id):
    from models import Investor, Startup
    investor = Investor.query.get_or_404(investor_id)
    startup = Startup.query.get_or_404(startup_id)
    if startup in investor.portfolio:
        investor.portfolio.remove(startup)
        db.session.commit()
        flash('Стартап удалён из портфеля!')
    return redirect(url_for('admin_edit_investor', investor_id=investor_id))

@app.route('/admin/investors/<int:investor_id>/portfolio/entry/add', methods=['POST'])
@admin_required
def admin_add_portfolio_entry(investor_id):
    from models import Investor, Startup, PortfolioEntry
    import json
    data = request.get_json()
    startup_id = int(data.get('startup_id'))
    amount = float(data.get('amount'))
    date_str = data.get('date')
    valuation = data.get('valuation')
    valuation = float(valuation) if valuation else None
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'success': False, 'error': 'Некорректная дата'}), 400
    investor = Investor.query.get_or_404(investor_id)
    startup = Startup.query.get_or_404(startup_id)
    # Проверка на дублирование
    exists = PortfolioEntry.query.filter_by(investor_id=investor_id, startup_id=startup_id).first()
    if exists:
        return jsonify({'success': False, 'error': 'Этот стартап уже есть в портфеле'}), 400
    entry = PortfolioEntry(
        investor_id=investor_id,
        startup_id=startup_id,
        amount=amount,
        date=date_obj,
        valuation=valuation
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'success': True, 'entry_id': entry.id})

@app.route('/admin/investors/<int:investor_id>/portfolio/entry/delete/<int:entry_id>', methods=['POST'])
@admin_required
def admin_delete_portfolio_entry(investor_id, entry_id):
    from models import PortfolioEntry
    entry = PortfolioEntry.query.get_or_404(entry_id)
    if entry.investor_id != investor_id:
        abort(403)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True) 