from fastapi import FastAPI, Request, Depends, Form, Path, Query, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn
import os
from typing import Optional
from sqlalchemy.orm import joinedload
from starlette.exceptions import HTTPException as StarletteHTTPException

from db import SessionLocal, Base, engine
from models import Startup, Investor, News, Podcast, Job, Event, Deal, User, Person, Country, City, StartupStage, Category, Author, PortfolioEntry
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from email.utils import parseaddr
import re

app = FastAPI()

# Подключение статики и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="stanbase_secret_2024", https_only=False)

# Удаляю GET-роуты /login и /register, оставляю только POST-обработку через модалки

@app.route("/login", methods=["POST"])
async def login(request: Request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        db = SessionLocal()
        user = db.query(User).filter_by(email=email, password=password).first()
        db.close()
        if user:
            request.session["user_id"] = user.id
            request.session["role"] = user.role
            request.session["username"] = user.username or user.email
            print("LOGIN SESSION SET:", dict(request.session))
            return JSONResponse({"success": True})
        else:
            return JSONResponse({"success": False, "error": "Неверный логин или пароль"})
    return JSONResponse({"success": False, "error": "Метод не разрешён"}, status_code=405)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    db = SessionLocal()
    countries = db.query(Country).order_by(Country.name).all()
    db.close()
    return templates.TemplateResponse("auth/register.html", {"request": request, "countries": countries, "session": request.session})

@app.route("/register", methods=["POST"])
async def register(request: Request):
    form = await request.form()
    first_name = form.get("first_name", "").strip()
    last_name = form.get("last_name", "").strip()
    country_id = form.get("country_id")
    city = form.get("city", "").strip()
    phone = form.get("phone", "").strip()
    email = form.get("email", "").strip().lower()
    telegram = form.get("telegram", "").strip()
    linkedin = form.get("linkedin", "").strip()
    role = form.get("role")
    password = form.get("password")
    agree1 = form.get("agree1")
    agree2 = form.get("agree2")
    is_ajax = request.headers.get("accept", "").lower().find("application/json") != -1
    # Валидация
    if not (first_name and last_name and country_id and city and phone and email and role and password and agree1 and agree2):
        error_msg = "Пожалуйста, заполните все обязательные поля и согласия."
        if is_ajax:
            return JSONResponse({"success": False, "error": error_msg}, status_code=400)
        return templates.TemplateResponse("auth/register.html", {"request": request, "countries": get_countries(), "error": error_msg, "session": request.session})
    if not re.match(r"^\+\d{10,15}$", phone):
        error_msg = "Телефон должен быть в формате +7XXXXXXXXXX"
        if is_ajax:
            return JSONResponse({"success": False, "error": error_msg}, status_code=400)
        return templates.TemplateResponse("auth/register.html", {"request": request, "countries": get_countries(), "error": error_msg, "session": request.session})
    if "@" not in parseaddr(email)[1]:
        error_msg = "Некорректный email."
        if is_ajax:
            return JSONResponse({"success": False, "error": error_msg}, status_code=400)
        return templates.TemplateResponse("auth/register.html", {"request": request, "countries": get_countries(), "error": error_msg, "session": request.session})
    db = SessionLocal()
    if db.query(User).filter_by(email=email).first():
        db.close()
        error_msg = "Пользователь с таким email уже существует."
        if is_ajax:
            return JSONResponse({"success": False, "error": error_msg}, status_code=400)
        return templates.TemplateResponse("auth/register.html", {"request": request, "countries": get_countries(), "error": error_msg, "session": request.session})
    user = User(
        email=email,
        password=password,
        role=role,
        first_name=first_name,
        last_name=last_name,
        country_id=country_id,
        city=city,
        phone=phone,
        telegram=telegram or None,
        linkedin=linkedin or None,
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    # Авторизация пользователя после регистрации
    request.session['user_id'] = user.id
    request.session['user_email'] = user.email
    request.session['user_name'] = user.first_name
    # Флеш-сообщение
    request.session['flash'] = 'Регистрация успешна! Вы вошли в систему.'
    if is_ajax:
        return JSONResponse({"success": True, "redirect": "/", "message": "Регистрация успешна! Вы вошли в систему."})
    return RedirectResponse(url="/", status_code=302)

def get_countries():
    db = SessionLocal()
    countries = db.query(Country).order_by(Country.name).all()
    db.close()
    return countries

@app.route("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

# Главная страница
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    print("INDEX SESSION:", dict(request.session))
    db = SessionLocal()
    startups = db.query(Startup).order_by(Startup.id.desc()).limit(20).all()
    investors = db.query(Investor).order_by(Investor.id.desc()).limit(20).all()
    news = db.query(News).order_by(News.date.desc()).limit(10).all()
    podcasts = db.query(Podcast).order_by(Podcast.date.desc()).limit(10).all()
    jobs = db.query(Job).order_by(Job.id.desc()).limit(10).all()
    events = db.query(Event).order_by(Event.date.desc()).limit(10).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "session": request.session, "startups": startups, "investors": investors, "news": news, "podcasts": podcasts, "jobs": jobs, "events": events})

# robots.txt
@app.get("/robots.txt")
def robots_txt():
    return RedirectResponse(url="/static/robots.txt")

# sitemap.xml
@app.get("/sitemap.xml")
def sitemap_xml():
    return RedirectResponse(url="/static/sitemap.xml")

@app.get("/startups", response_class=HTMLResponse)
def startups(request: Request, q: str = Query('', alias='q'), country: str = Query('', alias='country'), stage: str = Query('', alias='stage'), industry: str = Query('', alias='industry')):
    print("STARTUPS SESSION:", dict(request.session))
    db = SessionLocal()
    query = db.query(Startup)
    if q:
        query = query.filter(Startup.name.ilike(f'%{q}%'))
    if country:
        query = query.filter_by(country=country)
    if stage:
        query = query.filter_by(stage=stage)
    if industry:
        query = query.filter_by(industry=industry)
    startups = query.order_by(Startup.name).all()
    countries = [c[0] for c in db.query(Startup.country).distinct().order_by(Startup.country) if c[0]]
    stages = [s[0] for s in db.query(Startup.stage).distinct().order_by(Startup.stage) if s[0]]
    industries = [i[0] for i in db.query(Startup.industry).distinct().order_by(Startup.industry) if i[0]]
    db.close()
    return templates.TemplateResponse("public/startups/list.html", {"request": request, "session": request.session, "startups": startups, "countries": countries, "stages": stages, "industries": industries})

@app.get("/startup/{id}", response_class=HTMLResponse)
def startup_profile(request: Request, id: int = Path(...)):
    db = SessionLocal()
    startup = db.query(Startup).get(id)
    if not startup:
        db.close()
        raise HTTPException(status_code=404)
    team = list(startup.team)
    deals = list(startup.deals)
    jobs = list(startup.jobs)
    investors = db.query(Investor).all()
    investor_dict = {inv.name: inv for inv in investors}
    db.close()
    return templates.TemplateResponse(
        "public/startups/detail.html",
        {"request": request, "startup": startup, "team": team, "deals": deals, "jobs": jobs, "investor_dict": investor_dict, "session": request.session}
    )

@app.get("/investors", response_class=HTMLResponse)
def investors(request: Request, q: str = Query('', alias='q'), country: str = Query('', alias='country'), focus: str = Query('', alias='focus'), stages: str = Query('', alias='stages')):
    db = SessionLocal()
    query = db.query(Investor).options(joinedload(Investor.portfolio), joinedload(Investor.team))
    if q:
        query = query.filter(Investor.name.ilike(f'%{q}%'))
    if country:
        query = query.filter_by(country=country)
    if focus:
        query = query.filter(Investor.focus.ilike(f'%{focus}%'))
    if stages:
        query = query.filter(Investor.stages.ilike(f'%{stages}%'))
    investors = query.order_by(Investor.name).all()
    countries = [c[0] for c in db.query(Investor.country).distinct().order_by(Investor.country) if c[0]]
    # Собираем уникальные значения focus и stages (разбиваем по запятым)
    all_focus = set()
    all_stages = set()
    for f in db.query(Investor.focus).distinct():
        if f[0]:
            for part in f[0].split(','):
                val = part.strip()
                if val:
                    all_focus.add(val)
    for s in db.query(Investor.stages).distinct():
        if s[0]:
            for part in s[0].split(','):
                val = part.strip()
                if val:
                    all_stages.add(val)
    focus_list = sorted(all_focus)
    stages_list = sorted(all_stages)
    response = templates.TemplateResponse("public/investors/list.html", {"request": request, "session": request.session, "investors": investors, "countries": countries, "focus_list": focus_list, "stages_list": stages_list})
    db.close()
    return response

@app.get("/investor/{id}", response_class=HTMLResponse)
def investor_profile(request: Request, id: int = Path(...)):
    db = SessionLocal()
    investor = db.query(Investor).get(id)
    portfolio = list(investor.portfolio) if investor else []
    team = list(investor.team) if investor else []
    db.close()
    return templates.TemplateResponse("public/investors/detail.html", {"request": request, "session": request.session, "investor": investor, "portfolio": portfolio, "team": team})

@app.get("/news", response_class=HTMLResponse)
def news_list(request: Request):
    db = SessionLocal()
    news = db.query(News).order_by(News.date.desc()).all()
    db.close()
    return templates.TemplateResponse("public/news/list.html", {"request": request, "session": request.session, "news": news})

@app.get("/news/{id}", response_class=HTMLResponse)
def news_detail(request: Request, id: int = Path(...)):
    db = SessionLocal()
    news = db.query(News).get(id)
    db.close()
    return templates.TemplateResponse("public/news/detail.html", {"request": request, "session": request.session, "news": news})

@app.get("/events", response_class=HTMLResponse)
def events_list(request: Request):
    db = SessionLocal()
    events = db.query(Event).order_by(Event.date.desc()).all()
    db.close()
    return templates.TemplateResponse("public/events/list.html", {"request": request, "session": request.session, "events": events})

@app.get("/event/{id}", response_class=HTMLResponse)
def event_detail(request: Request, id: int = Path(...)):
    db = SessionLocal()
    event = db.query(Event).get(id)
    db.close()
    return templates.TemplateResponse("public/events/detail.html", {"request": request, "session": request.session, "event": event})

@app.get("/jobs", response_class=HTMLResponse)
def jobs_list(request: Request, q: str = Query('', alias='q'), city: str = Query('', alias='city'), job_type: str = Query('', alias='job_type'), startup: str = Query('', alias='startup')):
    db = SessionLocal()
    query = db.query(Job)
    if q:
        query = query.filter(Job.title.ilike(f'%{q}%'))
    if city:
        query = query.filter_by(city=city)
    if job_type:
        query = query.filter_by(job_type=job_type)
    if startup:
        query = query.filter_by(startup_id=startup)
    jobs = query.order_by(Job.id.desc()).all()
    cities = [c[0] for c in db.query(Job.city).distinct().order_by(Job.city) if c[0]]
    job_types = [t[0] for t in db.query(Job.job_type).distinct().order_by(Job.job_type) if t[0]]
    startups = db.query(Startup).order_by(Startup.name).all()
    db.close()
    return templates.TemplateResponse("public/jobs/list.html", {"request": request, "session": request.session, "jobs": jobs, "cities": cities, "job_types": job_types, "startups": startups})

@app.get("/job/{id}", response_class=HTMLResponse)
def job_detail(request: Request, id: int = Path(...)):
    db = SessionLocal()
    job = db.query(Job).get(id)
    startup = job.startup if job else None
    db.close()
    return templates.TemplateResponse("public/jobs/detail.html", {"request": request, "session": request.session, "job": job, "startup": startup})

@app.get("/podcasts", response_class=HTMLResponse)
def podcasts_list(request: Request):
    db = SessionLocal()
    podcasts = db.query(Podcast).order_by(Podcast.date.desc()).all()
    db.close()
    return templates.TemplateResponse("public/podcasts/list.html", {"request": request, "session": request.session, "podcasts": podcasts})

# --- Dashboard Investor ---
@app.get("/dashboard/investor", response_class=HTMLResponse)
async def dashboard_investor(request: Request):
    # Временно отключено для всех, кроме админов/модераторов
    if not (request.session.get('role') in ['admin', 'moderator']):
        return HTMLResponse("Доступ временно закрыт", status_code=403)
    # (Оставляю старую логику на будущее)
    # from models import User, Investor
    # user = None
    # investor = None
    # if request.session.get('user_id') and request.session.get('role') == 'investor':
    #     db = SessionLocal()
    #     user = db.query(User).get(request.session['user_id'])
    #     investor = db.query(Investor).get(user.investor_id)
    #     db.close()
    # else:
    #     return RedirectResponse(url="/login", status_code=302)
    # return templates.TemplateResponse("dashboard/investor.html", {"request": request, "user": user, "investor": investor})

# --- Dashboard Startuper ---
@app.get("/dashboard/startuper", response_class=HTMLResponse)
async def dashboard_startuper(request: Request):
    # Временно отключено для всех, кроме админов/модераторов
    if not (request.session.get('role') in ['admin', 'moderator']):
        return HTMLResponse("Доступ временно закрыт", status_code=403)
    # (Оставляю старую логику на будущее)
    # from models import User, Startup
    # user = None
    # startup = None
    # team = []
    # if request.session.get('user_id') and request.session.get('role') == 'startuper':
    #     db = SessionLocal()
    #     user = db.query(User).get(request.session['user_id'])
    #     startup = db.query(Startup).get(user.startup_id)
    #     if startup:
    #         team = list(startup.team)  # загружаем команду до закрытия сессии
    #     db.close()
    # else:
    #     return RedirectResponse(url="/login", status_code=302)
    # return templates.TemplateResponse("dashboard/startuper.html", {"request": request, "user": user, "startup": startup, "team": team})

# --- Инвестор: редактирование профиля ---
@app.route("/dashboard/investor/edit", methods=["GET", "POST"])
async def edit_investor(request: Request):
    from models import User, Investor
    if not request.session.get('user_id') or request.session.get('role') != 'investor':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    investor = db.query(Investor).get(user.investor_id)
    db.close()
    if not investor:
        return HTMLResponse("Инвестор не найден", status_code=404)
    if request.method == "POST":
        form = await request.form()
        investor.name = form.get('name')
        investor.description = form.get('description')
        investor.country = form.get('country')
        investor.focus = form.get('focus')
        investor.stages = form.get('stages')
        investor.website = form.get('website')
        db.commit()
        return RedirectResponse(url="/dashboard/investor", status_code=302)
    return templates.TemplateResponse("edit_investor.html", {"request": request, "investor": investor})

# --- Стартапер: редактирование профиля ---
@app.route("/dashboard/startuper/edit", methods=["GET", "POST"])
async def edit_startuper(request: Request):
    from models import User, Startup
    if not request.session.get('user_id') or request.session.get('role') != 'startuper':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    startup = db.query(Startup).get(user.startup_id)
    db.close()
    if not startup:
        return HTMLResponse("Стартап не найден", status_code=404)
    if request.method == "POST":
        form = await request.form()
        startup.name = form.get('name')
        startup.description = form.get('description')
        startup.country = form.get('country')
        startup.city = form.get('city')
        startup.stage = form.get('stage')
        startup.industry = form.get('industry')
        startup.website = form.get('website')
        db.commit()
        return RedirectResponse(url="/dashboard/startuper", status_code=302)
    return templates.TemplateResponse("edit_startuper.html", {"request": request, "startup": startup})

# --- Стартапер: добавление члена команды ---
@app.post("/dashboard/startuper/team/add")
async def add_team_member(request: Request):
    from models import User, Startup, Person
    if not request.session.get('user_id') or request.session.get('role') != 'startuper':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    startup = db.query(Startup).get(user.startup_id)
    db.close()
    if not startup:
        return HTMLResponse("Стартап не найден", status_code=404)
    form = await request.form()
    name = form.get('name')
    role = form.get('role')
    linkedin = form.get('linkedin')
    person = Person(name=name, role=role, linkedin=linkedin, country=startup.country)
    db.add(person)
    db.commit()
    startup.team.append(person)
    db.commit()
    return RedirectResponse(url="/dashboard/startuper", status_code=302)

# --- Стартапер: удаление члена команды ---
@app.post("/dashboard/startuper/team/delete/{person_id}")
async def delete_team_member(request: Request, person_id: int):
    from models import User, Startup, Person
    if not request.session.get('user_id') or request.session.get('role') != 'startuper':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    startup = db.query(Startup).get(user.startup_id)
    person = db.query(Person).get(person_id)
    db.close()
    if not startup or not person or person not in startup.team:
        return HTMLResponse("Член команды не найден", status_code=404)
    startup.team.remove(person)
    db.commit()
    return RedirectResponse(url="/dashboard/startuper", status_code=302)

# --- Инвестор: добавление стартапа в портфель ---
@app.post("/dashboard/investor/portfolio/add")
async def add_portfolio(request: Request):
    from models import User, Investor, Startup
    if not request.session.get('user_id') or request.session.get('role') != 'investor':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    investor = db.query(Investor).get(user.investor_id)
    form = await request.form()
    startup_id = int(form.get('startup_id'))
    startup = db.query(Startup).get(startup_id)
    db.close()
    if startup and startup not in investor.portfolio:
        investor.portfolio.append(startup)
        db.commit()
    return RedirectResponse(url="/dashboard/investor", status_code=302)

# --- Инвестор: удаление стартапа из портфеля ---
@app.post("/dashboard/investor/portfolio/delete/{startup_id}")
async def delete_portfolio(request: Request, startup_id: int):
    from models import User, Investor, Startup
    if not request.session.get('user_id') or request.session.get('role') != 'investor':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    investor = db.query(Investor).get(user.investor_id)
    startup = db.query(Startup).get(startup_id)
    db.close()
    if startup and startup in investor.portfolio:
        investor.portfolio.remove(startup)
        db.commit()
    return RedirectResponse(url="/dashboard/investor", status_code=302)

@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request, year: int = Query(None)):
    from models import Deal, Startup
    import datetime
    # Получаем все года, в которых были сделки
    db = SessionLocal()
    years = sorted({d.date.year for d in db.query(Deal) if d.date}, reverse=True)
    db.close()
    if not years:
        years = [datetime.date.today().year]
    if year is None:
        year = years[0]
    # Считаем по странам
    stats = {}
    db = SessionLocal()
    deals = db.query(Deal).filter(Deal.date != None).all()
    db.close()
    for d in deals:
        if d.date.year == year:
            country = d.startup.country if d.startup else 'Неизвестно'
            if country not in stats:
                stats[country] = {'sum': 0, 'count': 0}
            stats[country]['sum'] += d.amount or 0
            stats[country]['count'] += 1
    stats = sorted(stats.items(), key=lambda x: -x[1]['sum'])
    return templates.TemplateResponse("public/analytics.html", {"request": request, "session": request.session, "stats": stats, "years": years, "year": year})

def admin_required(request: Request):
    if not request.session.get('user_id') or request.session.get('role') not in ['admin', 'moderator']:
        return False
    return True

@app.get("/admin", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(request: Request):
    from models import User, Investor, Startup, News, Event, Job, Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    users = db.query(User).all()
    investors = db.query(Investor).all()
    startups = db.query(Startup).all()
    news = db.query(News).all()
    events = db.query(Event).all()
    jobs = db.query(Job).all()
    deals = db.query(Deal).all()
    db.close()
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "session": request.session, "users": users, "investors": investors, "startups": startups, "news": news, "events": events, "jobs": jobs, "deals": deals})

# --- Users CRUD ---
@app.get("/admin/users", response_class=HTMLResponse, name="admin_users")
async def admin_users(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page'), status_: str = Query('', alias='status')):
    from models import User, Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(User)
    if q:
        query = query.filter(User.username.ilike(f'%{q}%'))
    if status_:
        query = query.filter(User.status == status_)
    total = query.count()
    users = query.order_by(User.id).offset((page-1)*per_page).limit(per_page).all()
    countries = {c.id: c.name for c in db.query(Country).all()}
    db.close()
    return templates.TemplateResponse("admin/users/list.html", {"request": request, "session": request.session, "users": users, "countries": countries, "q": q, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/users/create", methods=["GET", "POST"], name="admin_create_user")
async def admin_create_user(request: Request):
    from models import User, Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    db = SessionLocal()
    countries = db.query(Country).order_by(Country.name).all()
    db.close()
    if request.method == "POST":
        form = await request.form()
        password = form.get('password')
        role = form.get('role')
        status_val = form.get('status')
        email = form.get('email')
        first_name = form.get('first_name')
        last_name = form.get('last_name')
        country_id = form.get('country_id')
        city = form.get('city')
        phone = form.get('phone')
        telegram = form.get('telegram')
        linkedin = form.get('linkedin')
        admin_email = request.session.get('username') or request.session.get('user_email')
        db = SessionLocal()
        if db.query(User).filter_by(email=email).first():
            error = 'Пользователь с таким email уже существует'
        else:
            if not password:
                error = 'Пароль обязателен при создании пользователя'
            else:
                user = User(email=email, password=password, role=role, status=status_val, first_name=first_name, last_name=last_name, country_id=country_id, city=city, phone=phone, telegram=telegram, linkedin=linkedin, created_by=admin_email)
                db.add(user)
                db.commit()
                db.close()
                return RedirectResponse(url="/admin/users", status_code=302)
        db.close()
        # Передаю введённые данные обратно в шаблон
        user_data = dict(email=email, role=role, status=status_val, first_name=first_name, last_name=last_name, country_id=country_id, city=city, phone=phone, telegram=telegram, linkedin=linkedin)
        return templates.TemplateResponse("admin/users/form.html", {"request": request, "error": error, "user": user_data, "countries": countries})
    return templates.TemplateResponse("admin/users/form.html", {"request": request, "error": error, "user": None, "countries": countries})

@app.get("/admin/users/edit/{user_id}", response_class=HTMLResponse, name="admin_edit_user")
async def admin_edit_user(request: Request, user_id: int):
    from models import User, Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(user_id)
    countries = db.query(Country).all()
    error = None
    db.close()
    return templates.TemplateResponse("admin/users/form.html", {"request": request, "error": error, "user": user, "countries": countries})

@app.post("/admin/users/edit/{user_id}", name="admin_edit_user_post")
async def admin_edit_user_post(request: Request, user_id: int):
    from models import User
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(user_id)
    form = await request.form()
    if form.get('password'):
        user.password = form.get('password')
    user.email = form.get('email')
    user.role = form.get('role')
    user.status = form.get('status')
    user.first_name = form.get('first_name')
    user.last_name = form.get('last_name')
    user.country_id = form.get('country_id')
    user.city = form.get('city')
    user.phone = form.get('phone')
    user.telegram = form.get('telegram')
    user.linkedin = form.get('linkedin')
    admin_email = request.session.get('username') or request.session.get('user_email')
    user.updated_by = admin_email
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/users", status_code=302)

@app.post("/admin/users/delete/{user_id}", name="admin_delete_user")
async def admin_delete_user(request: Request, user_id: int):
    from models import User
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(user_id)
    db.delete(user)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)

# --- Startups CRUD ---
@app.get("/admin/startups", response_class=HTMLResponse, name="admin_startups")
async def admin_startups(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Startup
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Startup)
    if q:
        query = query.filter(Startup.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(Startup.status == status)
    total = query.count()
    startups = query.order_by(Startup.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/startups/list.html", {"request": request, "startups": startups, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/startups/create", methods=["GET", "POST"], name="admin_create_startup")
async def admin_create_startup(request: Request):
    from models import Startup, Country, City, StartupStage, Category
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    db = SessionLocal()
    countries = db.query(Country).order_by(Country.name).all()
    cities = db.query(City).order_by(City.name).all()
    stages = db.query(StartupStage).order_by(StartupStage.name).all()
    industries = db.query(Category).order_by(Category.name).all()
    db.close()
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        description = form.get('description')
        country_id = int(form.get('country')) if form.get('country') else None
        city_id = int(form.get('city')) if form.get('city') else None
        stage_id = int(form.get('stage')) if form.get('stage') else None
        industry_id = int(form.get('industry')) if form.get('industry') else None
        status = form.get('status')
        founded_date_str = form.get('founded_date') or None
        website = form.get('website')
        founded_date = None
        if founded_date_str:
            try:
                founded_date = datetime.datetime.strptime(founded_date_str, "%Y-%m-%d").date()
            except Exception:
                error = "Некорректный формат даты (YYYY-MM-DD)"
        db = SessionLocal()
        country = db.query(Country).get(country_id) if country_id else None
        city = db.query(City).get(city_id) if city_id else None
        stage = db.query(StartupStage).get(stage_id) if stage_id else None
        industry = db.query(Category).get(industry_id) if industry_id else None
        created_by = request.session.get('username') if request.session.get('username') else None
        if not error:
            startup = Startup(
                name=name,
                description=description,
                country=country.name if country else '',
                city=city.name if city else '',
                stage=stage.name if stage else '',
                industry=industry.name if industry else '',
                status=status,
                founded_date=founded_date,
                website=website,
                created_by=created_by
            )
            db.add(startup)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/startups", status_code=302)
        db.close()
    return templates.TemplateResponse("admin/startups/form.html", {"request": request, "error": error, "startup": None, "countries": countries, "cities": cities, "stages": stages, "industries": industries})

@app.post("/admin/startups/delete/{startup_id}", name="admin_delete_startup")
async def admin_delete_startup(request: Request, startup_id: int):
    from models import Startup
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    startup = db.query(Startup).get(startup_id)
    if startup:
        db.delete(startup)
        db.commit()
    db.close()
    return RedirectResponse(url="/admin/startups", status_code=302)

# --- Startups ---
@app.get("/admin/startups/edit/{startup_id}", response_class=HTMLResponse, name="admin_edit_startup")
async def admin_edit_startup(request: Request, startup_id: int):
    from models import Startup, Country, City, StartupStage, Category
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    startup = db.query(Startup).get(startup_id)
    countries = db.query(Country).order_by(Country.name).all()
    cities = db.query(City).options(joinedload(City.country)).order_by(City.name).all()
    stages = db.query(StartupStage).order_by(StartupStage.name).all()
    industries = db.query(Category).order_by(Category.name).all()
    error = None
    team = startup.team if startup else []
    deals = startup.deals if startup else []
    jobs = startup.jobs if startup else []
    db.close()
    return templates.TemplateResponse("admin/startups/form.html", {"request": request, "error": error, "startup": startup, "team": team, "deals": deals, "jobs": jobs, "countries": countries, "cities": cities, "stages": stages, "industries": industries})

@app.post("/admin/startups/edit/{startup_id}", name="admin_edit_startup_post")
async def admin_edit_startup_post(request: Request, startup_id: int):
    from models import Startup
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    startup = db.query(Startup).get(startup_id)
    form = await request.form()
    startup.name = form.get('name')
    startup.description = form.get('description')
    startup.country = form.get('country')
    startup.city = form.get('city')
    startup.stage = form.get('stage')
    startup.industry = form.get('industry')
    founded_date_str = form.get('founded_date') or None
    if founded_date_str:
        try:
            startup.founded_date = datetime.datetime.strptime(founded_date_str, "%Y-%m-%d").date()
        except Exception:
            startup.founded_date = None
    else:
        startup.founded_date = None
    startup.website = form.get('website')
    startup.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/startups", status_code=302)

# --- Countries CRUD ---
@app.get("/admin/countries", response_class=HTMLResponse, name="admin_countries")
async def admin_countries(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Country)
    if q:
        query = query.filter(Country.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(Country.status == status)
    total = query.count()
    countries = query.order_by(Country.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/countries/list.html", {"request": request, "countries": countries, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/countries/create", methods=["GET", "POST"], name="admin_create_country")
async def admin_create_country(request: Request):
    from models import Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        status = form.get('status')
        db = SessionLocal()
        if db.query(Country).filter_by(name=name).first():
            error = 'Страна с таким названием уже существует'
        else:
            country = Country(name=name, status=status)
            db.add(country)
            db.commit()
            return RedirectResponse(url="/admin/countries", status_code=302)
    return templates.TemplateResponse("admin/countries/form.html", {"request": request, "error": error, "country": None})

@app.get("/admin/countries/edit/{country_id}", response_class=HTMLResponse, name="admin_edit_country")
async def admin_edit_country(request: Request, country_id: int):
    from models import Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    country = db.query(Country).get(country_id)
    error = None
    db.close()
    return templates.TemplateResponse("admin/countries/form.html", {"request": request, "error": error, "country": country})

@app.post("/admin/countries/edit/{country_id}", name="admin_edit_country_post")
async def admin_edit_country_post(request: Request, country_id: int):
    from models import Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    country = db.query(Country).get(country_id)
    form = await request.form()
    country.name = form.get('name')
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/countries", status_code=302)

@app.post("/admin/countries/delete/{country_id}", name="admin_delete_country")
async def admin_delete_country(request: Request, country_id: int):
    from models import Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    country = db.query(Country).get(country_id)
    db.delete(country)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/countries", status_code=302)

# --- Cities CRUD ---
@app.get("/admin/cities", response_class=HTMLResponse, name="admin_cities")
async def admin_cities(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import City, Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(City).options(joinedload(City.country))
    if q:
        query = query.filter(City.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(City.status == status)
    total = query.count()
    cities = query.order_by(City.id).offset((page-1)*per_page).limit(per_page).all()
    countries = db.query(Country).order_by(Country.name).all()
    import starlette.background
    response = templates.TemplateResponse("admin/cities/list.html", {"request": request, "cities": cities, "countries": countries, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})
    response.background = starlette.background.BackgroundTask(db.close)
    return response

@app.route("/admin/cities/create", methods=["GET", "POST"], name="admin_create_city")
async def admin_create_city(request: Request):
    from models import City
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        country_id = int(form.get('country_id'))
        status = form.get('status')
        db = SessionLocal()
        if db.query(City).filter_by(name=name, country_id=country_id).first():
            error = 'Город с таким названием в этой стране уже существует'
        else:
            city = City(name=name, country_id=country_id, status=status)
            db.add(city)
            db.commit()
            return RedirectResponse(url="/admin/cities", status_code=302)
    return templates.TemplateResponse("admin/cities/form.html", {"request": request, "error": error, "city": None})

@app.get("/admin/cities/edit/{city_id}", response_class=HTMLResponse, name="admin_edit_city")
async def admin_edit_city(request: Request, city_id: int):
    from models import City, Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    city = db.query(City).get(city_id)
    countries = db.query(Country).order_by(Country.name).all()
    error = None
    db.close()
    return templates.TemplateResponse("admin/cities/form.html", {"request": request, "error": error, "city": city, "countries": countries})

@app.post("/admin/cities/edit/{city_id}", name="admin_edit_city_post")
async def admin_edit_city_post(request: Request, city_id: int):
    from models import City
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    city = db.query(City).get(city_id)
    form = await request.form()
    city.name = form.get('name')
    city.country_id = int(form.get('country_id'))
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/cities", status_code=302)

@app.post("/admin/cities/delete/{city_id}", name="admin_delete_city")
async def admin_delete_city(request: Request, city_id: int):
    from models import City
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    city = db.query(City).get(city_id)
    db.delete(city)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/cities", status_code=302)

# --- Stages CRUD ---
@app.get("/admin/stages", response_class=HTMLResponse, name="admin_stages")
async def admin_stages(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import StartupStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(StartupStage)
    if q:
        query = query.filter(StartupStage.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(StartupStage.status == status)
    total = query.count()
    stages = query.order_by(StartupStage.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/stages/list.html", {"request": request, "stages": stages, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/stages/create", methods=["GET", "POST"], name="admin_create_stage")
async def admin_create_stage(request: Request):
    from models import StartupStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        status = form.get('status')
        db = SessionLocal()
        if db.query(StartupStage).filter_by(name=name).first():
            error = 'Этап с таким названием уже существует'
        else:
            stage = StartupStage(name=name, status=status)
            db.add(stage)
            db.commit()
            return RedirectResponse(url="/admin/stages", status_code=302)
    return templates.TemplateResponse("admin/stages/form.html", {"request": request, "error": error, "stage": None})

@app.get("/admin/stages/edit/{stage_id}", response_class=HTMLResponse, name="admin_edit_stage")
async def admin_edit_stage(request: Request, stage_id: int):
    from models import StartupStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    stage = db.query(StartupStage).get(stage_id)
    error = None
    db.close()
    return templates.TemplateResponse("admin/stages/form.html", {"request": request, "error": error, "stage": stage})

@app.post("/admin/stages/edit/{stage_id}", name="admin_edit_stage_post")
async def admin_edit_stage_post(request: Request, stage_id: int):
    from models import StartupStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    stage = db.query(StartupStage).get(stage_id)
    form = await request.form()
    stage.name = form.get('name')
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/stages", status_code=302)

@app.post("/admin/stages/delete/{stage_id}", name="admin_delete_stage")
async def admin_delete_stage(request: Request, stage_id: int):
    from models import StartupStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    stage = db.query(StartupStage).get(stage_id)
    db.delete(stage)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/stages", status_code=302)

# --- Categories CRUD ---
@app.get("/admin/categories", response_class=HTMLResponse, name="admin_categories")
async def admin_categories(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Category
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Category)
    if q:
        query = query.filter(Category.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(Category.status == status)
    total = query.count()
    categories = query.order_by(Category.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/categories/list.html", {"request": request, "categories": categories, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/categories/create", methods=["GET", "POST"], name="admin_create_category")
async def admin_create_category(request: Request):
    from models import Category
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        status = form.get('status')
        db = SessionLocal()
        if db.query(Category).filter_by(name=name).first():
            error = 'Категория с таким названием уже существует'
            db.close()
        else:
            category = Category(name=name, status=status)
            db.add(category)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/categories", status_code=302)
    return templates.TemplateResponse("admin/categories/form.html", {"request": request, "error": error, "category": None})

@app.get("/admin/categories/edit/{category_id}", response_class=HTMLResponse, name="admin_edit_category")
async def admin_edit_category(request: Request, category_id: int):
    from models import Category
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    category = db.query(Category).get(category_id)
    error = None
    db.close()
    return templates.TemplateResponse("admin/categories/form.html", {"request": request, "error": error, "category": category})

@app.post("/admin/categories/edit/{category_id}", name="admin_edit_category_post")
async def admin_edit_category_post(request: Request, category_id: int):
    from models import Category
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    category = db.query(Category).get(category_id)
    form = await request.form()
    category.name = form.get('name')
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/categories", status_code=302)

@app.post("/admin/categories/delete/{category_id}", name="admin_delete_category")
async def admin_delete_category(request: Request, category_id: int):
    from models import Category
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    category = db.query(Category).get(category_id)
    db.delete(category)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/categories", status_code=302)

# --- Authors CRUD ---
@app.get("/admin/authors", response_class=HTMLResponse, name="admin_authors")
async def admin_authors(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Author
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Author)
    if q:
        query = query.filter(Author.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(Author.status == status)
    total = query.count()
    authors = query.order_by(Author.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/authors/list.html", {"request": request, "authors": authors, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/authors/create", methods=["GET", "POST"], name="admin_create_author")
async def admin_create_author(request: Request):
    from models import Author
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        db = SessionLocal()
        if db.query(Author).filter_by(name=name).first():
            error = 'Автор с таким именем уже существует'
        else:
            author = Author(name=name)
            db.add(author)
            db.commit()
            return RedirectResponse(url="/admin/authors", status_code=302)
    return templates.TemplateResponse("admin/authors/form.html", {"request": request, "error": error, "author": None})

@app.get("/admin/authors/edit/{author_id}", response_class=HTMLResponse, name="admin_edit_author")
async def admin_edit_author(request: Request, author_id: int):
    from models import Author
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    author = db.query(Author).get(author_id)
    error = None
    db.close()
    return templates.TemplateResponse("admin/authors/form.html", {"request": request, "error": error, "author": author})

@app.post("/admin/authors/edit/{author_id}", name="admin_edit_author_post")
async def admin_edit_author_post(request: Request, author_id: int):
    from models import Author
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    author = db.query(Author).get(author_id)
    form = await request.form()
    author.name = form.get('name')
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/authors", status_code=302)

@app.post("/admin/authors/delete/{author_id}", name="admin_delete_author")
async def admin_delete_author(request: Request, author_id: int):
    from models import Author
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    author = db.query(Author).get(author_id)
    db.delete(author)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/authors", status_code=302)

# --- Jobs CRUD ---
@app.get("/admin/jobs", response_class=HTMLResponse, name="admin_jobs")
def admin_jobs(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Job, Startup
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Job)
    if q:
        query = query.filter(Job.title.ilike(f'%{q}%'))
    total = query.count()
    jobs = query.order_by(Job.id).offset((page-1)*per_page).limit(per_page).all()
    startups_list = db.query(Startup).all()
    startups = {s.id: s for s in startups_list}
    db.close()
    return templates.TemplateResponse("admin/jobs/list.html", {"request": request, "session": request.session, "jobs": jobs, "q": q, "per_page": per_page, "page": page, "total": total, "startups": startups})

@app.route("/admin/jobs/create", methods=["GET", "POST"], name="admin_create_job")
async def admin_create_job(request: Request):
    from models import Job, Startup, City
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    startup_id = request.query_params.get('startup_id')
    db = SessionLocal()
    startups = db.query(Startup).order_by(Startup.name).all()
    cities = db.query(City).options(joinedload(City.country)).order_by(City.name).all()
    db.close()
    if request.method == "POST":
        form = await request.form()
        title = form.get('title')
        description = form.get('description')
        city_id = int(form.get('city')) if form.get('city') else None
        job_type = form.get('job_type')
        startup_id_post = int(form.get('startup_id')) if form.get('startup_id') else None
        db = SessionLocal()
        if db.query(Job).filter_by(title=title, city_id=city_id, job_type=job_type, startup_id=startup_id_post).first():
            error = 'Вакансия с такими параметрами уже существует'
        else:
            job = Job(
                title=title,
                description=description,
                city_id=city_id,
                job_type=job_type,
                startup_id=startup_id_post
            )
            db.add(job)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/jobs", status_code=302)
        db.close()
    return templates.TemplateResponse("admin/jobs/form.html", {"request": request, "session": request.session, "error": error, "job": None, "startups": startups, "cities": cities, "startup_id": int(startup_id) if startup_id else None})

@app.get("/admin/jobs/edit/{job_id}", response_class=HTMLResponse, name="admin_edit_job")
async def admin_edit_job(request: Request, job_id: int):
    from models import Job, Startup, City
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    job = db.query(Job).options(joinedload(Job.startup)).get(job_id)
    startups = db.query(Startup).order_by(Startup.name).all()
    cities = db.query(City).order_by(City.name).all()
    error = None
    import starlette.background
    response = templates.TemplateResponse("admin/jobs/form.html", {"request": request, "session": request.session, "error": error, "job": job, "startups": startups, "cities": cities})
    response.background = starlette.background.BackgroundTask(db.close)
    return response

@app.post("/admin/jobs/edit/{job_id}", name="admin_edit_job_post")
async def admin_edit_job_post(request: Request, job_id: int):
    from models import Job
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    job = db.query(Job).get(job_id)
    form = await request.form()
    job.title = form.get('title')
    job.description = form.get('description')
    city_val = form.get('city')
    job.city_id = int(city_val) if city_val else None
    job.job_type = form.get('job_type')
    startup_val = form.get('startup_id')
    job.startup_id = int(startup_val) if startup_val else None
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/jobs", status_code=302)

@app.post("/admin/jobs/delete/{job_id}", name="admin_delete_job")
async def admin_delete_job(request: Request, job_id: int):
    from models import Job
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    job = db.query(Job).get(job_id)
    db.delete(job)
    db.commit()
    return RedirectResponse(url="/admin/jobs", status_code=302)

# --- News CRUD ---
@app.get("/admin/news", response_class=HTMLResponse, name="admin_news")
def admin_news(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import News
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(News).options(joinedload(News.author))
    if q:
        query = query.filter(News.title.ilike(f'%{q}%'))
    total = query.count()
    news = query.order_by(News.id).offset((page-1)*per_page).limit(per_page).all()
    response = templates.TemplateResponse("admin/news/list.html", {"request": request, "session": request.session, "news": news, "q": q, "per_page": per_page, "page": page, "total": total})
    db.close()
    return response

@app.route("/admin/news/create", methods=["GET", "POST"], name="admin_create_news")
async def admin_create_news(request: Request):
    from models import News
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        title = form.get('title')
        description = form.get('description')
        author_id = int(form.get('author_id'))
        category_id = int(form.get('category_id'))
        db = SessionLocal()
        if db.query(News).filter_by(title=title, author_id=author_id, category_id=category_id).first():
            error = 'Новость с такими параметрами уже существует'
        else:
            news = News(
                title=title,
                description=description,
                author_id=author_id,
                category_id=category_id
            )
            db.add(news)
            db.commit()
            return RedirectResponse(url="/admin/news", status_code=302)
    return templates.TemplateResponse("admin/news/form.html", {"request": request, "session": request.session, "error": error, "news": None})

@app.get("/admin/news/edit/{news_id}", response_class=HTMLResponse, name="admin_edit_news")
async def admin_edit_news(request: Request, news_id: int):
    from models import News
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    news = db.query(News).get(news_id)
    error = None
    db.close()
    return templates.TemplateResponse("admin/news/form.html", {"request": request, "session": request.session, "error": error, "news": news})

@app.post("/admin/news/edit/{news_id}", name="admin_edit_news_post")
async def admin_edit_news_post(request: Request, news_id: int):
    from models import News
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    news = db.query(News).get(news_id)
    form = await request.form()
    news.title = form.get('title')
    news.description = form.get('description')
    news.author_id = int(form.get('author_id'))
    news.category_id = int(form.get('category_id'))
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/news", status_code=302)

@app.post("/admin/news/delete/{news_id}", name="admin_delete_news")
async def admin_delete_news(request: Request, news_id: int):
    from models import News
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    news = db.query(News).get(news_id)
    db.delete(news)
    db.commit()
    return RedirectResponse(url="/admin/news", status_code=302)

# --- Deals CRUD ---
@app.get("/admin/deals", response_class=HTMLResponse, name="admin_deals")
def admin_deals(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Deal)
    if q:
        query = query.filter(Deal.title.ilike(f'%{q}%'))
    total = query.count()
    deals = query.order_by(Deal.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/deals/list.html", {"request": request, "session": request.session, "deals": deals, "q": q, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/deals/create", methods=["GET", "POST"], name="admin_create_deal")
async def admin_create_deal(request: Request):
    from models import Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        title = form.get('title')
        description = form.get('description')
        date = form.get('date')
        amount = form.get('amount')
        startup_id = int(form.get('startup_id'))
        investor_id = int(form.get('investor_id'))
        db = SessionLocal()
        if db.query(Deal).filter_by(title=title, startup_id=startup_id, investor_id=investor_id).first():
            error = 'Сделка с такими параметрами уже существует'
        else:
            deal = Deal(
                title=title,
                description=description,
                date=date,
                amount=amount,
                startup_id=startup_id,
                investor_id=investor_id
            )
            db.add(deal)
            db.commit()
            return RedirectResponse(url="/admin/deals", status_code=302)
    return templates.TemplateResponse("admin/deals/form.html", {"request": request, "session": request.session, "error": error, "deal": None})

@app.get("/admin/deals/edit/{deal_id}", response_class=HTMLResponse, name="admin_edit_deal")
async def admin_edit_deal(request: Request, deal_id: int):
    from models import Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    deal = db.query(Deal).get(deal_id)
    error = None
    db.close()
    return templates.TemplateResponse("admin/deals/form.html", {"request": request, "session": request.session, "error": error, "deal": deal})

@app.post("/admin/deals/edit/{deal_id}", name="admin_edit_deal_post")
async def admin_edit_deal_post(request: Request, deal_id: int):
    from models import Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    deal = db.query(Deal).get(deal_id)
    form = await request.form()
    deal.title = form.get('title')
    deal.description = form.get('description')
    deal.date = form.get('date')
    deal.amount = form.get('amount')
    deal.startup_id = int(form.get('startup_id'))
    deal.investor_id = int(form.get('investor_id'))
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/deals", status_code=302)

@app.post("/admin/deals/delete/{deal_id}", name="admin_delete_deal")
async def admin_delete_deal(request: Request, deal_id: int):
    from models import Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    deal = db.query(Deal).get(deal_id)
    db.delete(deal)
    db.commit()
    return RedirectResponse(url="/admin/deals", status_code=302)

@app.get("/admin/investors", response_class=HTMLResponse, name="admin_investors")
async def admin_investors(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Investor
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Investor)
    if q:
        query = query.filter(Investor.name.ilike(f'%{q}%'))
    total = query.count()
    investors = query.order_by(Investor.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/investors/list.html", {"request": request, "session": request.session, "investors": investors, "q": q, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/investors/create", methods=["GET", "POST"], name="admin_create_investor")
async def admin_create_investor(request: Request):
    from models import Investor
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    today = datetime.date.today()
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        description = form.get('description')
        country = form.get('country')
        focus = form.get('focus')
        stages = form.get('stages')
        website = form.get('website')
        type_ = form.get('type')
        db = SessionLocal()
        investor = Investor(
            name=name,
            description=description,
            country=country,
            focus=focus,
            stages=stages,
            website=website,
            type=type_
        )
        db.add(investor)
        db.commit()
        db.close()
        return RedirectResponse(url="/admin/investors", status_code=302)
    return templates.TemplateResponse("admin/investors/form.html", {"request": request, "session": request.session, "investor": None, "error": error, "today": today})

@app.get("/admin/investors/edit/{investor_id}", response_class=HTMLResponse, name="admin_edit_investor")
async def admin_edit_investor(request: Request, investor_id: int):
    from models import Investor
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    investor = db.query(Investor)\
        .options(joinedload(Investor.portfolio_entries).joinedload(PortfolioEntry.startup), joinedload(Investor.team))\
        .get(investor_id)
    error = None
    today = datetime.date.today()
    import starlette.background
    response = templates.TemplateResponse("admin/investors/form.html", {"request": request, "session": request.session, "investor": investor, "error": error, "today": today})
    response.background = starlette.background.BackgroundTask(db.close)
    return response

@app.post("/admin/investors/edit/{investor_id}", name="admin_edit_investor_post")
async def admin_edit_investor_post(request: Request, investor_id: int):
    from models import Investor
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    investor = db.query(Investor).get(investor_id)
    form = await request.form()
    investor.name = form.get('name')
    investor.description = form.get('description')
    investor.country = form.get('country')
    investor.focus = form.get('focus')
    investor.stages = form.get('stages')
    investor.website = form.get('website')
    investor.type = form.get('type')
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/investors", status_code=302)

@app.post("/admin/investors/delete/{investor_id}", name="admin_delete_investor")
async def admin_delete_investor(request: Request, investor_id: int):
    from models import Investor
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    investor = db.query(Investor).get(investor_id)
    db.delete(investor)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/investors", status_code=302)

@app.get("/admin/startup_search")
async def admin_startup_search(q: str = Query('', alias='q')):
    db = SessionLocal()
    query = db.query(Startup)
    if q:
        query = query.filter(Startup.name.ilike(f"%{q}%"))
    startups = query.order_by(Startup.name).limit(20).all()
    results = []
    for s in startups:
        country_code = (s.country or '').strip().upper()[:2]
        text = f"{s.name}, {country_code}" if country_code else s.name
        results.append({"id": s.id, "text": text})
    db.close()
    return {"results": results}

@app.get("/admin/city_search")
async def admin_city_search(q: str = Query('', alias='q')):
    from models import City, Country
    db = SessionLocal()
    query = db.query(City)
    if q:
        query = query.filter(City.name.ilike(f"%{q}%"))
    cities = query.order_by(City.name).limit(20).all()
    results = []
    for c in cities:
        country = db.query(Country).get(c.country_id)
        country_code = (country.name or '').strip().upper()[:2] if country else ''
        text = f"{c.name}, {country_code}" if country_code else c.name
        results.append({"id": c.id, "text": text, "country": country.name if country else ''})
    db.close()
    return {"results": results}

# --- Добавление участника команды из админки ---
@app.post("/admin/team/create", name="admin_create_team_member")
async def admin_create_team_member(request: Request):
    from models import Person, Startup
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    form = await request.form()
    name = form.get('name')
    role = form.get('role')
    linkedin = form.get('linkedin')
    startup_id = int(request.query_params.get('startup_id')) if request.query_params.get('startup_id') else None
    db = SessionLocal()
    person = Person(name=name, role=role, linkedin=linkedin)
    db.add(person)
    db.commit()
    if startup_id:
        startup = db.query(Startup).get(startup_id)
        if startup:
            startup.team.append(person)
            db.commit()
    db.close()
    return RedirectResponse(url=f"/admin/startups/edit/{startup_id}", status_code=302)

@app.get("/admin/admins", response_class=HTMLResponse, name="admin_admins")
def admin_admins(request: Request):
    db = SessionLocal()
    users = db.query(User).filter(User.role.in_(["admin", "moderator"])).all()
    db.close()
    return templates.TemplateResponse("admin/users/admins.html", {"request": request, "users": users})

@app.exception_handler(404)
async def not_found(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse("404.html", {"request": request, "session": request.session}, status_code=404)

@app.get("/")
def root():
    return "Stanbase API is running"

# Гарантируем создание таблиц при любом запуске
Base.metadata.create_all(bind=engine)

# --- Автоматическое создание тестовых стартапов и пользователей ---
def create_test_startups_and_users():
    from db import SessionLocal
    from models import User, Startup, Country
    session = SessionLocal()
    # Создать тестовый стартап, если его нет
    if not session.query(Startup).first():
        startup = Startup(
            name="CerebraAI",
            description="AI для диагностики инсульта и других заболеваний по КТ/МРТ. Лидер в HealthTech Казахстана.",
            country="Казахстан",
            city="Алматы",
            stage="Growth",
            industry="HealthTech",
            website="https://cerebraai.ai"
        )
        session.add(startup)
        session.commit()
    # Админ
    if not session.query(User).filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            email="admin@stanbase.test",
            password="admin123",
            role="admin",
            first_name="Admin",
            last_name="Stanbase",
            country_id=1,
            city="Алматы",
            phone="+77001234567",
            status="active"
        )
        session.add(admin_user)
        session.commit()
    # Модератор
    if not session.query(User).filter_by(username="moderator").first():
        moderator_user = User(
            username="moderator",
            email="moderator@stanbase.test",
            password="mod123",
            role="moderator",
            first_name="Mod",
            last_name="Stanbase",
            country_id=1,
            city="Алматы",
            phone="+77001234568",
            status="active"
        )
        session.add(moderator_user)
        session.commit()
    # Стартапер
    if not session.query(User).filter_by(username="startuper").first():
        startup = session.query(Startup).first()
        if startup:
            startuper_user = User(
                username="startuper",
                email="startuper@stanbase.test",
                password="startuper123",
                role="startuper",
                first_name="Start",
                last_name="Stanbase",
                country_id=1,
                city="Алматы",
                phone="+77001234569",
                startup_id=startup.id,
                status="active"
            )
            session.add(startuper_user)
            session.commit()
    session.close()

create_test_startups_and_users()

# --- Автоматическое создание тестовых данных для всех сущностей ---
def create_full_test_data():
    from db import SessionLocal
    from models import User, Startup, Country, City, Category, StartupStage, Author, Investor, News, Podcast, Event, Deal, Person
    session = SessionLocal()
    # Country
    if not session.query(Country).first():
        countries = [Country(name=n) for n in ["Казахстан", "Узбекистан", "Кыргызстан", "Таджикистан", "Туркменистан"]]
        session.add_all(countries)
        session.commit()
    country_dict = {c.name: c.id for c in session.query(Country).all()}
    if not country_dict:
        print("Нет ни одной страны в базе, пользователи не будут созданы!")
        session.close()
        return
    kz_id = country_dict.get("Казахстан") or list(country_dict.values())[0]
    # City
    if not session.query(City).first():
        cities = [City(name=n, country_id=kz_id) for n in ["Алматы", "Астана", "Ташкент", "Бишкек", "Душанбе"]]
        session.add_all(cities)
        session.commit()
    city_dict = {c.name: c.id for c in session.query(City).all()}
    almata_id = city_dict.get("Алматы") or list(city_dict.values())[0]
    # Category
    if not session.query(Category).first():
        cats = [Category(name=n) for n in ["Fintech", "HealthTech", "HRTech", "E-commerce", "SaaS"]]
        session.add_all(cats)
        session.commit()
    # StartupStage
    if not session.query(StartupStage).first():
        stages = [StartupStage(name=n) for n in ["Seed", "Growth", "Scale", "Idea"]]
        session.add_all(stages)
        session.commit()
    # Author
    if not session.query(Author).first():
        authors = [Author(name=n, description=f"Автор {n}") for n in ["Иванов", "Петров", "Сидоров"]]
        session.add_all(authors)
        session.commit()
    # Startup
    if not session.query(Startup).first():
        startups = [Startup(name=f"Startup {i}", description=f"Описание {i}", country="Казахстан", city="Алматы", stage="Seed", industry="Fintech", website=f"https://startup{i}.com") for i in range(1, 4)]
        session.add_all(startups)
        session.commit()
    startup = session.query(Startup).first()
    # Investor
    if not session.query(Investor).first():
        investors = [Investor(name=f"Investor {i}", description=f"Инвестор {i}", country="Казахстан", focus="Fintech", stages="Seed", website=f"https://investor{i}.com", type="angel") for i in range(1, 4)]
        session.add_all(investors)
        session.commit()
    # User
    if not session.query(User).filter_by(username="admin").first():
        admin_user = User(username="admin", email="admin@stanbase.test", password="admin123", role="admin", first_name="Admin", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234567", status="active")
        session.add(admin_user)
        session.commit()
    if not session.query(User).filter_by(username="moderator").first():
        moderator_user = User(username="moderator", email="moderator@stanbase.test", password="mod123", role="moderator", first_name="Mod", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234568", status="active")
        session.add(moderator_user)
        session.commit()
    if not session.query(User).filter_by(username="startuper").first():
        if startup:
            startuper_user = User(username="startuper", email="startuper@stanbase.test", password="startuper123", role="startuper", first_name="Start", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234569", startup_id=startup.id, status="active")
            session.add(startuper_user)
            session.commit()
    # News
    if not session.query(News).first():
        news = [News(title=f"Новость {i}", summary=f"Кратко {i}", date="2024-01-0{}".format(i), content=f"Текст новости {i}", status="active") for i in range(1, 4)]
        session.add_all(news)
        session.commit()
    # Podcast
    if not session.query(Podcast).first():
        podcasts = [Podcast(title=f"Подкаст {i}", description=f"Описание подкаста {i}", youtube_url="https://youtube.com/", date="2024-01-0{}".format(i), status="active") for i in range(1, 4)]
        session.add_all(podcasts)
        session.commit()
    # Event
    if not session.query(Event).first():
        events = [Event(title=f"Мероприятие {i}", description=f"Описание события {i}", date="2024-01-0{}".format(i), format="Онлайн", location="Алматы", registration_url="https://event.com/", status="active") for i in range(1, 4)]
        session.add_all(events)
        session.commit()
    # Deal
    if not session.query(Deal).first():
        deals = [Deal(type="investment", amount=10000*i, date="2024-01-0{}".format(i), currency="USD", startup_id=startup.id if startup else None, investors="Investor 1", status="active") for i in range(1, 4)]
        session.add_all(deals)
        session.commit()
    # Person
    if not session.query(Person).first():
        persons = [Person(name=f"Person {i}", country="Казахстан", linkedin="https://linkedin.com/in/person{i}", role="CEO", status="active") for i in range(1, 4)]
        session.add_all(persons)
        session.commit()
    session.close()

create_full_test_data()

if __name__ == "__main__":
    print('SERVER STARTED')
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 