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
import subprocess
from fastapi import APIRouter
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError, InternalError

from db import SessionLocal, Base, engine
from models import Company, Investor, News, Podcast, Job, Event, Deal, User, Person, Country, City, Category, Author, PortfolioEntry, CompanyStage
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from email.utils import parseaddr
import re
import unicodedata

app = FastAPI()

# Подключение статики и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="stanbase_secret_2024", https_only=False)

def generate_slug(title):
    """Генерирует SEO-friendly slug из заголовка новости"""
    # Нормализация Unicode (убираем диакритические знаки)
    title = unicodedata.normalize('NFKD', title)
    
    # Транслитерация кириллицы в латиницу
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Заменяем кириллицу на латиницу
    for cyr, lat in cyrillic_to_latin.items():
        title = title.replace(cyr, lat)
    
    # Приводим к нижнему регистру
    title = title.lower()
    
    # Заменяем все символы кроме букв и цифр на дефисы
    title = re.sub(r'[^a-z0-9\s-]', '', title)
    
    # Заменяем пробелы на дефисы
    title = re.sub(r'\s+', '-', title)
    
    # Убираем множественные дефисы
    title = re.sub(r'-+', '-', title)
    
    # Убираем дефисы в начале и конце
    title = title.strip('-')
    
    return title

# Глобальный обработчик SQLAlchemy ошибок
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    print(f"SQLAlchemy error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
    )

@app.exception_handler(InternalError)
async def internal_error_handler(request: Request, exc: InternalError):
    print(f"Internal database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal database error"}
    )

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
    try:
        companies = db.query(Company).order_by(Company.id.desc()).limit(20).all()
        investors = db.query(Investor).order_by(Investor.id.desc()).limit(20).all()
        news = db.query(News).order_by(News.date.desc()).limit(10).all()
        podcasts = db.query(Podcast).order_by(Podcast.date.desc()).limit(10).all()
        jobs = db.query(Job).order_by(Job.id.desc()).limit(10).all()
        events = db.query(Event).order_by(Event.date.desc()).limit(10).all()
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        # Возвращаем пустые списки в случае ошибки
        companies = []
        investors = []
        news = []
        podcasts = []
        jobs = []
        events = []
    finally:
        db.close()
    return templates.TemplateResponse("index.html", {"request": request, "session": request.session, "companies": companies, "investors": investors, "news": news, "podcasts": podcasts, "jobs": jobs, "events": events})

# robots.txt
@app.get("/robots.txt")
def robots_txt():
    return RedirectResponse(url="/static/robots.txt")

# sitemap.xml
@app.get("/sitemap.xml")
def sitemap_xml():
    return RedirectResponse(url="/static/sitemap.xml")

@app.get("/companies", response_class=HTMLResponse)
def companies(request: Request, q: str = Query('', alias='q'), country: str = Query('', alias='country'), stage: str = Query('', alias='stage'), industry: str = Query('', alias='industry')):
    print("COMPANIES SESSION:", dict(request.session))
    db = SessionLocal()
    query = db.query(Company)
    if q:
        query = query.filter(Company.name.ilike(f'%{q}%'))
    if country:
        query = query.filter_by(country=country)
    if stage:
        query = query.filter_by(stage=stage)
    if industry:
        query = query.filter_by(industry=industry)
    companies = query.order_by(Company.name).all()
    countries = [c[0] for c in db.query(Company.country).distinct().order_by(Company.country) if c[0]]
    stages = [s[0] for s in db.query(Company.stage).distinct().order_by(Company.stage) if s[0]]
    industries = [i[0] for i in db.query(Company.industry).distinct().order_by(Company.industry) if i[0]]
    db.close()
    return templates.TemplateResponse("public/companies/list.html", {"request": request, "session": request.session, "companies": companies, "countries": countries, "stages": stages, "industries": industries})

@app.get("/company/{id}", response_class=HTMLResponse)
def company_profile(request: Request, id: int = Path(...)):
    db = SessionLocal()
    company = db.query(Company).options(joinedload(Company.deals).joinedload(Deal.currency)).get(id)
    if not company:
        db.close()
        raise HTTPException(status_code=404)
    team = list(company.team)
    deals = list(company.deals)
    jobs = list(company.jobs)
    investors = db.query(Investor).all()
    investor_dict = {inv.name: inv for inv in investors}

    # --- Логика подбора похожих компаний ---
    similar_query = db.query(Company).filter(Company.id != company.id)
    filters = []
    if company.country:
        filters.append(Company.country == company.country)
    if company.stage:
        filters.append(Company.stage == company.stage)
    if company.industry:
        filters.append(Company.industry == company.industry)
    if filters:
        similar_query = similar_query.filter(or_(*filters))
    similar = similar_query.limit(6).all()

    db.close()
    return templates.TemplateResponse(
        "public/companies/detail.html",
        {"request": request, "company": company, "team": team, "deals": deals, "jobs": jobs, "investor_dict": investor_dict, "session": request.session, "similar": similar}
    )

@app.get("/investors", response_class=HTMLResponse)
def investors(request: Request, q: str = Query('', alias='q'), country: str = Query('', alias='country'), focus: str = Query('', alias='focus'), stages: str = Query('', alias='stages')):
    db = SessionLocal()
    try:
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
    except Exception as e:
        print(f"Ошибка при загрузке инвесторов: {e}")
        investors = []
        countries = []
        focus_list = []
        stages_list = []
    finally:
        db.close()
    response = templates.TemplateResponse("public/investors/list.html", {"request": request, "session": request.session, "investors": investors, "countries": countries, "focus_list": focus_list, "stages_list": stages_list})
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

@app.get("/news/{slug}", response_class=HTMLResponse)
def news_detail(request: Request, slug: str = Path(...)):
    from models import News, Event
    from sqlalchemy import and_
    from sqlalchemy.orm import joinedload
    from datetime import datetime
    
    db = SessionLocal()
    
    # Основная новость с загрузкой автора по slug
    news = db.query(News).options(joinedload(News.author)).filter(News.slug == slug).first()
    
    if not news:
        db.close()
        raise HTTPException(status_code=404, detail="Новость не найдена")
    
    # Другие новости (исключая текущую)
    other_news = db.query(News).filter(News.id != news.id).order_by(News.date.desc()).limit(5).all()
    
    # Ближайшие мероприятия (будущие)
    upcoming_events = db.query(Event).filter(
        and_(Event.date >= datetime.now(), Event.status == 'active')
    ).order_by(Event.date.asc()).limit(3).all()
    
    db.close()
    
    return templates.TemplateResponse("public/news/detail.html", {
        "request": request, 
        "session": request.session, 
        "news": news,
        "other_news": other_news,
        "upcoming_events": upcoming_events
    })

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
def jobs_list(request: Request, q: str = Query('', alias='q'), city: str = Query('', alias='city'), job_type: str = Query('', alias='job_type'), company: str = Query('', alias='company')):
    db = SessionLocal()
    query = db.query(Job)
    if q:
        query = query.filter(Job.title.ilike(f'%{q}%'))
    if city:
        query = query.filter_by(city=city)
    if job_type:
        query = query.filter_by(job_type=job_type)
    if company:
        query = query.filter_by(company_id=company)
    jobs = query.order_by(Job.id.desc()).all()
    cities = [c[0] for c in db.query(Job.city).distinct().order_by(Job.city) if c[0]]
    job_types = [t[0] for t in db.query(Job.job_type).distinct().order_by(Job.job_type) if t[0]]
    companies = db.query(Company).order_by(Company.name).all()
    db.close()
    return templates.TemplateResponse("public/jobs/list.html", {"request": request, "session": request.session, "jobs": jobs, "cities": cities, "job_types": job_types, "companies": companies})

@app.get("/job/{id}", response_class=HTMLResponse)
def job_detail(request: Request, id: int = Path(...)):
    db = SessionLocal()
    job = db.query(Job).get(id)
    company = job.company if job else None
    db.close()
    return templates.TemplateResponse("public/jobs/detail.html", {"request": request, "session": request.session, "job": job, "company": company})

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
    # from models import User, Company
    # user = None
    # startup = None
    # team = []
    # if request.session.get('user_id') and request.session.get('role') == 'startuper':
    #     db = SessionLocal()
    #     user = db.query(User).get(request.session['user_id'])
    #     company = db.query(Company).get(user.company_id)
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
    from models import User, Company
    if not request.session.get('user_id') or request.session.get('role') != 'startuper':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    company = db.query(Company).get(user.company_id)
    db.close()
    if not company:
        return HTMLResponse("Стартап не найден", status_code=404)
    if request.method == "POST":
        form = await request.form()
        company.name = form.get('name')
        company.description = form.get('description')
        company.country = form.get('country')
        company.city = form.get('city')
        company.stage = form.get('stage')
        company.industry = form.get('industry')
        company.website = form.get('website')
        db.commit()
        return RedirectResponse(url="/dashboard/startuper", status_code=302)
    return templates.TemplateResponse("edit_startuper.html", {"request": request, "company": company})

# --- Стартапер: добавление члена команды ---
@app.post("/dashboard/startuper/team/add")
async def add_team_member(request: Request):
    from models import User, Company, Person
    if not request.session.get('user_id') or request.session.get('role') != 'startuper':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    company = db.query(Company).get(user.company_id)
    db.close()
    if not company:
        return HTMLResponse("Стартап не найден", status_code=404)
    form = await request.form()
    name = form.get('name')
    role = form.get('role')
    linkedin = form.get('linkedin')
    person = Person(name=name, role=role, linkedin=linkedin, country=company.country)
    db.add(person)
    db.commit()
    company.team.append(person)
    db.commit()
    return RedirectResponse(url="/dashboard/startuper", status_code=302)

# --- Стартапер: удаление члена команды ---
@app.post("/dashboard/startuper/team/delete/{person_id}")
async def delete_team_member(request: Request, person_id: int):
    from models import User, Company, Person
    if not request.session.get('user_id') or request.session.get('role') != 'startuper':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    company = db.query(Company).get(user.company_id)
    person = db.query(Person).get(person_id)
    db.close()
    if not company or not person or person not in company.team:
        return HTMLResponse("Член команды не найден", status_code=404)
    company.team.remove(person)
    db.commit()
    return RedirectResponse(url="/dashboard/startuper", status_code=302)

# --- Инвестор: добавление стартапа в портфель ---
@app.post("/dashboard/investor/portfolio/add")
async def add_portfolio(request: Request):
    from models import User, Investor, Company
    if not request.session.get('user_id') or request.session.get('role') != 'investor':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    investor = db.query(Investor).get(user.investor_id)
    form = await request.form()
    company_id = int(form.get('company_id'))
    company = db.query(Company).get(company_id)
    db.close()
    if company and company not in investor.portfolio:
        investor.portfolio.append(company)
        db.commit()
    return RedirectResponse(url="/dashboard/investor", status_code=302)

# --- Инвестор: удаление стартапа из портфеля ---
@app.post("/dashboard/investor/portfolio/delete/{company_id}")
async def delete_portfolio(request: Request, company_id: int):
    from models import User, Investor, Company
    if not request.session.get('user_id') or request.session.get('role') != 'investor':
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    user = db.query(User).get(request.session['user_id'])
    investor = db.query(Investor).get(user.investor_id)
    company = db.query(Company).get(company_id)
    db.close()
    if company and company in investor.portfolio:
        investor.portfolio.remove(company)
        db.commit()
    return RedirectResponse(url="/dashboard/investor", status_code=302)

@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request, year: int = Query(None)):
    from models import Deal, Company
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
    from sqlalchemy.orm import joinedload
    deals = db.query(Deal).options(joinedload(Deal.company)).filter(Deal.date != None).all()
    db.close()
    for d in deals:
        if d.date.year == year:
            country = d.company.country if d.company else 'Неизвестно'
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
    from models import User, Investor, News, Event, Job, Deal, Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    users = db.query(User).all()
    companies = db.query(Company).all()
    investors = db.query(Investor).all()
    news = db.query(News).all()
    events = db.query(Event).all()
    jobs = db.query(Job).all()
    deals = db.query(Deal).all()
    db.close()
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "session": request.session, "users": users, "companies": companies, "investors": investors, "news": news, "events": events, "jobs": jobs, "deals": deals})

# --- Users CRUD ---
@app.get("/admin/users", response_class=HTMLResponse, name="admin_users")
async def admin_users(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page'), status_: str = Query('', alias='status')):
    from models import User, Country
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(User)
    if q:
        query = query.filter(User.email.ilike(f'%{q}%'))
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
        db = SessionLocal()
        if db.query(User).filter_by(email=email).first():
            error = 'Пользователь с таким email уже существует'
        else:
            if not password:
                error = 'Пароль обязателен при создании пользователя'
            else:
                user = User(email=email, password=password, role=role, status=status_val, first_name=first_name, last_name=last_name, country_id=country_id, city=city, phone=phone, telegram=telegram, linkedin=linkedin)
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
    user.updated_by = request.session.get('user_email')
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

# --- Companies CRUD ---
@app.get("/admin/companies", response_class=HTMLResponse, name="admin_companies")
async def admin_startups(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Company)
    if q:
        query = query.filter(Company.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(Company.status == status)
    total = query.count()
    companies = query.order_by(Company.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/companies/list.html", {"request": request, "companies": companies, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/companies/create", methods=["GET", "POST"], name="admin_create_company")
async def admin_create_startup(request: Request):
    from models import Company, Country, City
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    db = SessionLocal()
    countries = db.query(Country).order_by(Country.name).all()
    cities = db.query(City).order_by(City.name).all()
    db.close()
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        description = form.get('description')
        country_id = int(form.get('country')) if form.get('country') else None
        city_id = int(form.get('city')) if form.get('city') else None
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
        created_by = request.session.get('user_email')
        if not error:
            company = Company(
                name=name,
                description=description,
                country=country.name if country else '',
                city=city.name if city else '',
                status=status,
                founded_date=founded_date,
                website=website,
                created_by=created_by
            )
            db.add(company)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/companies", status_code=302)
        db.close()
    return templates.TemplateResponse("admin/companies/form.html", {"request": request, "error": error, "company": None, "countries": countries, "cities": cities})

@app.post("/admin/companies/delete/{company_id}", name="admin_delete_company")
async def admin_delete_startup(request: Request, company_id: int):
    from models import Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    company = db.query(Company).get(company_id)
    if company:
        db.delete(company)
        db.commit()
    db.close()
    return RedirectResponse(url="/admin/companies", status_code=302)

# --- Companies ---
@app.get("/admin/companies/edit/{company_id}", response_class=HTMLResponse, name="admin_edit_company")
async def admin_edit_startup(request: Request, company_id: int):
    from models import Company, Country, City
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    company = db.query(Company).get(company_id)
    countries = db.query(Country).order_by(Country.name).all()
    cities = db.query(City).options(joinedload(City.country)).order_by(City.name).all()
    error = None
    team = company.team if company else []
    deals = company.deals if company else []
    jobs = company.jobs if company else []
    db.close()
    return templates.TemplateResponse("admin/companies/form.html", {"request": request, "error": error, "company": company, "team": team, "deals": deals, "jobs": jobs, "countries": countries, "cities": cities})

@app.post("/admin/companies/edit/{company_id}", name="admin_edit_company_post")
async def admin_edit_startup_post(request: Request, company_id: int):
    from models import Company
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    company = db.query(Company).get(company_id)
    form = await request.form()
    company.name = form.get('name')
    company.description = form.get('description')
    company.country = form.get('country')
    company.city = form.get('city')
    company.status = form.get('status')
    company.stage = form.get('stage')
    company.industry = form.get('industry')
    company.website = form.get('website')
    company.updated_at = datetime.datetime.utcnow()

    # --- обработка логотипа ---
    logo_file = form.get('logo')
    if logo_file and hasattr(logo_file, 'filename') and logo_file.filename:
        filename = f"company_{company_id}_{logo_file.filename}"
        save_dir = os.path.join("static", "logos")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        contents = await logo_file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        company.logo = f"/static/logos/{filename}"

    db.commit()
    db.close()
    active_tab = form.get('active_tab') or 'main'
    return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab={active_tab}", status_code=302)

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
    from models import Job, Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Job)
    if q:
        query = query.filter(Job.title.ilike(f'%{q}%'))
    total = query.count()
    jobs = query.order_by(Job.id).offset((page-1)*per_page).limit(per_page).all()
    companies_list = db.query(Company).all()
    companies = {s.id: s for s in companies_list}
    db.close()
    return templates.TemplateResponse("admin/jobs/list.html", {"request": request, "session": request.session, "jobs": jobs, "q": q, "per_page": per_page, "page": page, "total": total, "companies": companies})

@app.route("/admin/jobs/create", methods=["GET", "POST"], name="admin_create_job")
async def admin_create_job(request: Request):
    from models import Job, Company, City
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    company_id = request.query_params.get('company_id')
    db = SessionLocal()
    companies = db.query(Company).order_by(Company.name).all()
    cities = db.query(City).options(joinedload(City.country)).order_by(City.name).all()
    db.close()
    if request.method == "POST":
        form = await request.form()
        title = form.get('title')
        description = form.get('description')
        city = form.get('city')
        job_type = form.get('job_type')
        company_id_post = int(form.get('company_id')) if form.get('company_id') else None
        status = form.get('status')
        contact = form.get('contact')
        db = SessionLocal()
        if db.query(Job).filter_by(title=title, city=city, job_type=job_type, company_id=company_id_post).first():
            error = 'Вакансия с такими параметрами уже существует'
        else:
            job = Job(
                title=title,
                description=description,
                city=city,
                job_type=job_type,
                company_id=company_id_post,
                status=status,
                contact=contact
            )
            db.add(job)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/jobs", status_code=302)
        db.close()
    return templates.TemplateResponse("admin/jobs/form.html", {"request": request, "session": request.session, "error": error, "job": None, "companies": companies, "cities": cities, "company_id": int(company_id) if company_id else None})

@app.get("/admin/jobs/edit/{job_id}", response_class=HTMLResponse, name="admin_edit_job")
async def admin_edit_job(request: Request, job_id: int):
    from models import Job, Company, City
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    job = db.query(Job).options(joinedload(Job.company)).get(job_id)
    companies = db.query(Company).order_by(Company.name).all()
    cities = db.query(City).order_by(City.name).all()
    error = None
    import starlette.background
    response = templates.TemplateResponse("admin/jobs/form.html", {"request": request, "session": request.session, "error": error, "job": job, "companies": companies, "cities": cities})
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
    job.city = form.get('city')
    job.job_type = form.get('job_type')
    company_val = form.get('company_id')
    job.company_id = int(company_val) if company_val else None
    job.status = form.get('status')
    job.contact = form.get('contact')
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
            # Генерируем slug из заголовка
            slug = generate_slug(title)
            
            # Проверяем уникальность slug
            counter = 1
            original_slug = slug
            while db.query(News).filter_by(slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            news = News(
                title=title,
                slug=slug,
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
    title = form.get('title')
    news.title = title
    news.description = form.get('description')
    news.author_id = int(form.get('author_id'))
    news.category_id = int(form.get('category_id'))
    
    # Обновляем slug если изменился заголовок
    new_slug = generate_slug(title)
    if new_slug != news.slug:
        # Проверяем уникальность нового slug
        counter = 1
        original_slug = new_slug
        while db.query(News).filter(News.slug == new_slug, News.id != news_id).first():
            new_slug = f"{original_slug}-{counter}"
            counter += 1
        news.slug = new_slug
    
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
def admin_deals(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Deal
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Deal).options(joinedload(Deal.company), joinedload(Deal.currency))
    if q:
        query = query.filter(Deal.type.ilike(f'%{q}%'))
    if status:
        query = query.filter(Deal.status == status)
    total = query.count()
    deals = query.order_by(Deal.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/deals/list.html", {"request": request, "session": request.session, "deals": deals, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/deals/create", methods=["GET", "POST"], name="admin_create_deal")
async def admin_create_deal(request: Request):
    from models import Deal, Company, Investor, Currency
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    db = SessionLocal()
    companies = db.query(Company).all()
    investors = db.query(Investor).all()
    currencies = db.query(Currency).filter_by(status='active').all()
    
    if request.method == "POST":
        form = await request.form()
        deal_type = form.get('type')
        amount_str = form.get('amount', '').replace(' ', '').replace(',', '')
        valuation_str = form.get('valuation', '').replace(' ', '').replace(',', '')
        date = form.get('date')
        currency_id = int(form.get('currency_id')) if form.get('currency_id') else None
        company_id = int(form.get('company_id'))
        investors_list = form.getlist('investors')  # Множественный выбор
        investors_str = ', '.join(investors_list) if investors_list else ''
        status = form.get('status')
        
        # Преобразуем строки в числа
        amount = int(amount_str) if amount_str else None
        valuation = int(valuation_str) if valuation_str else None
        
        if db.query(Deal).filter_by(type=deal_type, company_id=company_id).first():
            error = 'Сделка с такими параметрами уже существует'
        else:
            deal = Deal(
                type=deal_type,
                amount=amount,
                valuation=valuation,
                date=date,
                currency_id=currency_id,
                company_id=company_id,
                investors=investors_str,
                status=status
            )
            db.add(deal)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/deals", status_code=302)
    
    db.close()
    return templates.TemplateResponse("admin/deals/form.html", {"request": request, "session": request.session, "error": error, "deal": None, "companies": companies, "investors": investors, "currencies": currencies})

@app.get("/admin/deals/edit/{deal_id}", response_class=HTMLResponse, name="admin_edit_deal")
async def admin_edit_deal(request: Request, deal_id: int):
    from models import Deal, Company, Investor, Currency
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    deal = db.query(Deal).options(joinedload(Deal.company), joinedload(Deal.currency)).get(deal_id)
    companies = db.query(Company).all()
    investors = db.query(Investor).all()
    currencies = db.query(Currency).filter_by(status='active').all()
    error = None
    db.close()
    return templates.TemplateResponse("admin/deals/form.html", {"request": request, "session": request.session, "error": error, "deal": deal, "companies": companies, "investors": investors, "currencies": currencies})

@app.post("/admin/deals/edit/{deal_id}", name="admin_edit_deal_post")
async def admin_edit_deal_post(request: Request, deal_id: int):
    from models import Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    deal = db.query(Deal).get(deal_id)
    form = await request.form()
    deal.type = form.get('type')
    
    # Обработка чисел с разделителями
    amount_str = form.get('amount', '').replace(' ', '').replace(',', '')
    valuation_str = form.get('valuation', '').replace(' ', '').replace(',', '')
    
    deal.amount = int(amount_str) if amount_str else None
    deal.valuation = int(valuation_str) if valuation_str else None
    deal.date = form.get('date')
    deal.currency_id = int(form.get('currency_id')) if form.get('currency_id') else None
    deal.company_id = int(form.get('company_id'))
    investors_list = form.getlist('investors')  # Множественный выбор
    deal.investors = ', '.join(investors_list) if investors_list else ''
    deal.status = form.get('status')
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
        .options(joinedload(Investor.portfolio_entries).joinedload(PortfolioEntry.company), joinedload(Investor.team))\
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

    # --- обработка логотипа ---
    logo_file = form.get('logo')
    if logo_file and hasattr(logo_file, 'filename') and logo_file.filename:
        import os
        filename = f"investor_{investor_id}_{logo_file.filename}"
        save_dir = os.path.join("static", "logos")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        contents = await logo_file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        investor.logo = f"/static/logos/{filename}"

    db.commit()
    db.close()
    return RedirectResponse(url=f"/admin/investors/edit/{investor_id}", status_code=302)

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

@app.get("/admin/company_search")
async def admin_startup_search(q: str = Query('', alias='q')):
    db = SessionLocal()
    query = db.query(Company)
    if q:
        query = query.filter(Company.name.ilike(f"%{q}%"))
    companies = query.order_by(Company.name).limit(20).all()
    results = []
    for s in companies:
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
    from models import Person, Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    form = await request.form()
    name = form.get('name')
    role = form.get('role')
    linkedin = form.get('linkedin')
    company_id = int(request.query_params.get('company_id')) if request.query_params.get('company_id') else None
    db = SessionLocal()
    person = Person(name=name, role=role, linkedin=linkedin)
    db.add(person)
    db.commit()
    if company_id:
        company = db.query(Company).get(company_id)
        if company:
            company.team.append(person)
            db.commit()
    db.close()
    return RedirectResponse(url=f"/admin/companies/edit/{company_id}", status_code=302)

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

# --- Автоматическое создание тестовых данных для всех сущностей ---
def create_full_test_data():
    from db import SessionLocal
    from models import User, Company, Country, City, Category, Author, Investor, News, Podcast, Event, Deal, Person
    session = SessionLocal()
    # Country
    try:
        if not session.query(Country).first():
            countries = [Country(name=n) for n in ["Казахстан", "Узбекистан", "Кыргызстан", "Таджикистан", "Туркменистан"]]
            session.add_all(countries)
            session.commit()
    except Exception as e:
        print(f"Ошибка при создании стран: {e}")
        session.rollback()
    country_dict = {c.name: c.id for c in session.query(Country).all()}
    if not country_dict:
        print("Нет ни одной страны в базе, пользователи не будут созданы!")
        session.close()
        return
    kz_id = country_dict.get("Казахстан") or list(country_dict.values())[0]
    print(f"country_id для тестовых пользователей: {kz_id}")
    # City
    try:
        if not session.query(City).first():
            cities = [City(name=n, country_id=kz_id) for n in ["Алматы", "Астана", "Ташкент", "Бишкек", "Душанбе"]]
            session.add_all(cities)
            session.commit()
    except Exception as e:
        print(f"Ошибка при создании городов: {e}")
        session.rollback()
    city_dict = {c.name: c.id for c in session.query(City).all()}
    almata_id = city_dict.get("Алматы") or list(city_dict.values())[0]
    # Category
    try:
        if not session.query(Category).first():
            cats = [Category(name=n) for n in ["Fintech", "HealthTech", "HRTech", "E-commerce", "SaaS"]]
            session.add_all(cats)
            session.commit()
    except Exception as e:
        print(f"Ошибка при создании категорий: {e}")
        session.rollback()
    # Company (реальные примеры ЦА, максимально живые)
    try:
        if not session.query(Company).first():
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
    except Exception as e:
        print(f"Ошибка при создании компаний: {e}")
        session.rollback()
    # News (реальные/реалистичные)
    try:
        if not session.query(News).first():
            news = [
                News(title="CerebraAI вошла в топ-200 стартапов TechCrunch Battlefield", summary="Казахстанский HealthTech-стартап получил международное признание.", date="2024-06-01", content="CerebraAI, ведущий AI-стартап в сфере медицины, вошёл в топ-200 стартапов TechCrunch Battlefield.", status="active"),
                News(title="Uzum привлек $50 млн инвестиций и стал первым единорогом Узбекистана", summary="Оценка Uzum превысила $1 млрд — это первый единорог страны.", date="2024-05-15", content="Экосистема Uzum объявила о привлечении $50 млн и достижении оценки $1 млрд.", status="active"),
                News(title="Tezbus запустил онлайн-бронирование билетов в Кыргызстане", summary="Tezbus расширяет сервисы по всей Центральной Азии.", date="2024-04-20", content="Tezbus Group запустила новый сервис для онлайн-бронирования междугородних поездок.", status="active"),
                News(title="Voicy внедряет распознавание казахской речи в госуслугах", summary="Voicy помогает цифровизации госуслуг в Казахстане.", date="2024-03-10", content="Voicy интегрировала свою AI-платформу в ряд государственных сервисов Казахстана.", status="active"),
                News(title="FORBOSSINFO запускает мультисервисную платформу для бизнеса в ЦА", summary="FORBOSSINFO выходит на рынок Казахстана и Узбекистана.", date="2024-03-01", content="FORBOSSINFO — первая мультисервисная платформа для бизнеса в Центральной Азии, стартовала в Казахстане.", status="active"),
                News(title="Pamir Group внедряет водородные технологии в Таджикистане", summary="Pamir Group реализует проекты по зелёной энергетике.", date="2024-02-15", content="Pamir Group OÜ внедряет решения по производству зелёного водорода и модернизации энергетики Таджикистана.", status="active")
            ]
            session.add_all(news)
            session.commit()
    except Exception as e:
        print(f"Ошибка при создании новостей: {e}")
        session.rollback()
    # User
    try:
        if not session.query(User).filter_by(email="admin@stanbase.test").first():
            print(f"Создаём admin с country_id={kz_id}")
            admin_user = User(email="admin@stanbase.test", password="admin123", role="admin", first_name="Admin", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234567", status="active")
            session.add(admin_user)
            session.commit()
        if not session.query(User).filter_by(email="moderator@stanbase.test").first():
            print(f"Создаём moderator с country_id={kz_id}")
            moderator_user = User(email="moderator@stanbase.test", password="mod123", role="moderator", first_name="Mod", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234568", status="active")
            session.add(moderator_user)
            session.commit()
        if not session.query(User).filter_by(email="startuper@stanbase.test").first():
            companies = session.query(Company).all()
            if companies:
                print(f"Создаём startuper с country_id={kz_id}")
                startuper_user = User(email="startuper@stanbase.test", password="startuper123", role="startuper", first_name="Start", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234569", company_id=companies[0].id, status="active")
                session.add(startuper_user)
                session.commit()
    except Exception as e:
        print(f"Ошибка при создании тестовых пользователей: {e}")
        session.rollback()
        # Создаем новую сессию после ошибки
        session.close()
        session = SessionLocal()
    # Person
    try:
        if not session.query(Person).first():
            persons = [Person(name=f"Person {i}", country="Казахстан", linkedin="https://linkedin.com/in/person{i}", role="CEO", status="active") for i in range(1, 4)]
            session.add_all(persons)
            session.commit()
    except Exception as e:
        print(f"Ошибка при создании тестовых персон: {e}")
        session.rollback()
    finally:
        session.close()

create_full_test_data()

router = APIRouter()

@router.get("/run-migration")
def run_migration():
    try:
        import migrate_to_prod
        migrate_to_prod.migrate_production_database()
        return {"success": True, "message": "Миграция выполнена успешно"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/import-data")
def import_data(data: dict):
    try:
        import import_data
        import_data.import_data_from_dict(data)
        return {"success": True, "message": "Данные импортированы успешно"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/test-db")
def test_db():
    """Тестовый эндпоинт для проверки базы данных"""
    db = SessionLocal()
    try:
        # Проверяем количество записей
        companies_count = db.query(Company).count()
        investors_count = db.query(Investor).count()
        news_count = db.query(News).count()
        events_count = db.query(Event).count()
        
        # Проверяем структуру таблиц
        company_columns = [c.name for c in Company.__table__.columns]
        investor_columns = [c.name for c in Investor.__table__.columns]
        
        return {
            "success": True,
            "counts": {
                "companies": companies_count,
                "investors": investors_count,
                "news": news_count,
                "events": events_count
            },
            "columns": {
                "company": company_columns,
                "investor": investor_columns
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()

app.include_router(router)

@app.get("/admin/currencies", response_class=HTMLResponse, name="admin_currencies")
async def admin_currencies(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Currency
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Currency)
    if q:
        query = query.filter(Currency.name.ilike(f'%{q}%') | Currency.code.ilike(f'%{q}%'))
    if status:
        query = query.filter(Currency.status == status)
    total = query.count()
    currencies = query.order_by(Currency.code).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/currencies/list.html", {"request": request, "session": request.session, "currencies": currencies, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/currencies/create", methods=["GET", "POST"], name="admin_create_currency")
async def admin_create_currency(request: Request):
    from models import Currency
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        code = form.get('code').upper()
        name = form.get('name')
        symbol = form.get('symbol')
        db = SessionLocal()
        if db.query(Currency).filter_by(code=code).first():
            error = 'Валюта с таким кодом уже существует'
        else:
            currency = Currency(code=code, name=name, symbol=symbol)
            db.add(currency)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/currencies", status_code=302)
        db.close()
    return templates.TemplateResponse("admin/currencies/form.html", {"request": request, "session": request.session, "error": error, "currency": None})

@app.get("/admin/currencies/edit/{currency_id}", response_class=HTMLResponse, name="admin_edit_currency")
async def admin_edit_currency(request: Request, currency_id: int):
    from models import Currency
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    currency = db.query(Currency).get(currency_id)
    error = None
    db.close()
    return templates.TemplateResponse("admin/currencies/form.html", {"request": request, "session": request.session, "error": error, "currency": currency})

@app.post("/admin/currencies/edit/{currency_id}", name="admin_edit_currency_post")
async def admin_edit_currency_post(request: Request, currency_id: int):
    from models import Currency
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    currency = db.query(Currency).get(currency_id)
    form = await request.form()
    currency.code = form.get('code').upper()
    currency.name = form.get('name')
    currency.symbol = form.get('symbol')
    currency.status = form.get('status')
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/currencies", status_code=302)

@app.post("/admin/currencies/delete/{currency_id}", name="admin_delete_currency")
async def admin_delete_currency(request: Request, currency_id: int):
    from models import Currency
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    currency = db.query(Currency).get(currency_id)
    db.delete(currency)
    db.commit()
    db.close()
    return RedirectResponse(url="/admin/currencies", status_code=302)

@app.get("/admin/company_stages", response_class=HTMLResponse, name="admin_company_stages")
async def admin_company_stages(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import CompanyStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(CompanyStage)
    if q:
        query = query.filter(CompanyStage.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(CompanyStage.status == status)
    total = query.count()
    stages = query.order_by(CompanyStage.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/company_stages/list.html", {"request": request, "stages": stages, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/company_stages/create", methods=["GET", "POST"], name="admin_create_company_stage")
async def admin_create_company_stage(request: Request):
    from models import CompanyStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        status = form.get('status')
        db = SessionLocal()
        if db.query(CompanyStage).filter_by(name=name).first():
            error = 'Стадия с таким названием уже существует.'
        else:
            stage = CompanyStage(name=name, status=status)
            db.add(stage)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/company_stages", status_code=302)
        db.close()
        return templates.TemplateResponse("admin/company_stages/form.html", {"request": request, "stage": None, "error": error})
    return templates.TemplateResponse("admin/company_stages/form.html", {"request": request, "stage": None, "error": error})

@app.route("/admin/company_stages/edit/{stage_id}", methods=["GET", "POST"], name="admin_edit_company_stage")
async def admin_edit_company_stage(request: Request, stage_id: int):
    from models import CompanyStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    stage = db.query(CompanyStage).get(stage_id)
    error = None
    if not stage:
        db.close()
        return HTMLResponse("Стадия не найдена", status_code=404)
    if request.method == "POST":
        form = await request.form()
        stage.name = form.get('name')
        stage.status = form.get('status')
        db.commit()
        db.close()
        return RedirectResponse(url="/admin/company_stages", status_code=302)
    db.close()
    return templates.TemplateResponse("admin/company_stages/form.html", {"request": request, "stage": stage, "error": error})

@app.post("/admin/company_stages/delete/{stage_id}", name="admin_delete_company_stage")
async def admin_delete_company_stage(request: Request, stage_id: int):
    from models import CompanyStage
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    stage = db.query(CompanyStage).get(stage_id)
    if stage:
        db.delete(stage)
        db.commit()
    db.close()
    return RedirectResponse(url="/admin/company_stages", status_code=302)

@app.get("/admin/companies", response_class=HTMLResponse, name="admin_companies")
async def admin_companies(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Company)
    if q:
        query = query.filter(Company.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(Company.status == status)
    total = query.count()
    companies = query.order_by(Company.id).offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/companies/list.html", {"request": request, "companies": companies, "q": q, "status": status, "per_page": per_page, "page": page, "total": total})

@app.route("/admin/companies/create", methods=["GET", "POST"], name="admin_create_company")
async def admin_create_company(request: Request):
    from models import Company, Country, City
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    error = None
    db = SessionLocal()
    countries = db.query(Country).order_by(Country.name).all()
    cities = db.query(City).order_by(City.name).all()
    db.close()
    if request.method == "POST":
        form = await request.form()
        name = form.get('name')
        description = form.get('description')
        country = form.get('country')
        city = form.get('city')
        status = form.get('status')
        stage = form.get('stage')
        industry = form.get('industry')
        website = form.get('website')
        db = SessionLocal()
        company = Company(
            name=name,
            description=description,
            country=country,
            city=city,
            status=status,
            stage=stage,
            industry=industry,
            website=website
        )
        db.add(company)
        db.commit()
        db.close()
        return RedirectResponse(url="/admin/companies", status_code=302)
    return templates.TemplateResponse("admin/companies/form.html", {"request": request, "company": None, "countries": countries, "cities": cities, "error": error})

@app.post("/admin/companies/delete/{company_id}", name="admin_delete_company")
async def admin_delete_company(request: Request, company_id: int):
    from models import Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    company = db.query(Company).get(company_id)
    if company:
        db.delete(company)
        db.commit()
    db.close()
    return RedirectResponse(url="/admin/companies", status_code=302)

@app.get("/admin/companies/edit/{company_id}", response_class=HTMLResponse, name="admin_edit_company")
async def admin_edit_company(request: Request, company_id: int):
    from models import Company, Country, City
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    company = db.query(Company).get(company_id)
    countries = db.query(Country).order_by(Country.name).all()
    cities = db.query(City).options(joinedload(City.country)).order_by(City.name).all()
    error = None
    team = company.team if company else []
    jobs = company.jobs if company else []
    db.close()
    return templates.TemplateResponse("admin/companies/form.html", {"request": request, "company": company, "countries": countries, "cities": cities, "error": error, "team": team, "jobs": jobs})

@app.post("/admin/companies/edit/{company_id}", name="admin_edit_company_post")
async def admin_edit_company_post(request: Request, company_id: int):
    from models import Company
    import datetime
    import os
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    company = db.query(Company).get(company_id)
    form = await request.form()
    company.name = form.get('name')
    company.description = form.get('description')
    company.country = form.get('country')
    company.city = form.get('city')
    company.status = form.get('status')
    company.stage = form.get('stage')
    company.industry = form.get('industry')
    company.website = form.get('website')
    company.updated_at = datetime.datetime.utcnow()

    # --- обработка логотипа ---
    logo_file = form.get('logo')
    if logo_file and hasattr(logo_file, 'filename') and logo_file.filename:
        filename = f"company_{company_id}_{logo_file.filename}"
        save_dir = os.path.join("static", "logos")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        contents = await logo_file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        company.logo = f"/static/logos/{filename}"

    db.commit()
    db.close()
    active_tab = form.get('active_tab') or 'main'
    return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab={active_tab}", status_code=302)

if __name__ == "__main__":
    print('SERVER STARTED')
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 