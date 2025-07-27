from fastapi import FastAPI, Request, Depends, Form, Path, Query, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn
import os
import secrets
from typing import Optional
from sqlalchemy.orm import joinedload
from starlette.exceptions import HTTPException as StarletteHTTPException
import subprocess
from fastapi import APIRouter
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError, InternalError
from datetime import datetime, timedelta

from db import SessionLocal, Base, engine
from models import Company, Investor, News, Podcast, Job, Event, Deal, User, Person, Country, City, Category, Author, PortfolioEntry, CompanyStage, Feedback
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from email.utils import parseaddr
import re
import unicodedata
from utils.security import verify_password, get_password_hash, create_access_token, verify_token
from utils.csrf import get_csrf_token, verify_csrf_token
from utils.image_processor import ImageProcessor
from services.api import api_router
from services.notifications import NotificationService, NotificationTemplates
from services.comments import CommentService, CommentValidator
from services.cache import QueryCache, CacheInvalidator
from services.pagination import PaginationHelper, DatabasePagination

app = FastAPI()

# Подключение статики и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Middleware для генерации session_id для CSRF защиты
from starlette.middleware.base import BaseHTTPMiddleware

class SessionIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Проверяем, что сессия доступна
        try:
            if hasattr(request, 'session') and request.session:
                if "session_id" not in request.session:
                    request.session["session_id"] = secrets.token_hex(16)
        except AssertionError:
            # SessionMiddleware еще не инициализирован, пропускаем
            pass
        response = await call_next(request)
        return response

app.add_middleware(SessionMiddleware, secret_key="stanbase_secret_2024", https_only=False)
app.add_middleware(SessionIDMiddleware)

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
        user = db.query(User).filter_by(email=email).first()
        db.close()
        
        if user and verify_password(password, user.password):
            request.session["user_id"] = user.id
            request.session["role"] = user.role
            request.session["user_email"] = user.email
            request.session["user_name"] = user.first_name
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
        password=get_password_hash(password),
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
@app.get("/search", response_class=HTMLResponse)
async def universal_search(request: Request, q: str = Query('', alias='q')):
    """
    Универсальный поиск по всем основным сущностям:
    - Компании (name, description, industry, country, city, stage)
    - Инвесторы (name, description, focus, country, stages)
    - Новости (title, summary, content)
    - Вакансии (title, description, city, job_type, contact)
    """
    if not q or not q.strip():
        return RedirectResponse(url="/")
    q = q.strip()
    db = SessionLocal()
    try:
        from sqlalchemy import or_
        # Компании
        companies = db.query(Company).filter(
            Company.status == 'active',
            or_(
                Company.name.ilike(f'%{q}%'),
                Company.description.ilike(f'%{q}%'),
                Company.industry.ilike(f'%{q}%'),
                Company.country.ilike(f'%{q}%'),
                Company.city.ilike(f'%{q}%'),
                Company.stage.ilike(f'%{q}%')
            )
        ).order_by(Company.id.desc()).limit(20).all()

        # Инвесторы
        investors = db.query(Investor).filter(
            Investor.status == 'active',
            or_(
                Investor.name.ilike(f'%{q}%'),
                Investor.description.ilike(f'%{q}%'),
                Investor.focus.ilike(f'%{q}%'),
                Investor.country.ilike(f'%{q}%'),
                Investor.stages.ilike(f'%{q}%')
            )
        ).order_by(Investor.id.desc()).limit(20).all()

        # Новости
        news = db.query(News).options(joinedload(News.author)).filter(
            News.status == 'active',
            or_(
                News.title.ilike(f'%{q}%'),
                News.summary.ilike(f'%{q}%'),
                News.content.ilike(f'%{q}%')
            )
        ).order_by(News.date.desc()).limit(20).all()

        # Вакансии
        jobs = db.query(Job).options(joinedload(Job.company)).filter(
            Job.status == 'active',
            or_(
                Job.title.ilike(f'%{q}%'),
                Job.description.ilike(f'%{q}%'),
                Job.city.ilike(f'%{q}%'),
                Job.job_type.ilike(f'%{q}%'),
                Job.contact.ilike(f'%{q}%')
            )
        ).order_by(Job.id.desc()).limit(20).all()

        total_results = len(companies) + len(investors) + len(news) + len(jobs)
        print(f"[SEARCH] Запрос: '{q}' | Компании: {len(companies)}, Инвесторы: {len(investors)}, Новости: {len(news)}, Вакансии: {len(jobs)}")
    except Exception as e:
        print(f"[SEARCH ERROR] Ошибка при поиске: {e}")
        companies = []
        investors = []
        news = []
        jobs = []
        total_results = 0
    finally:
        db.close()
    return templates.TemplateResponse("public/search.html", {
        "request": request,
        "session": request.session,
        "query": q,
        "companies": companies,
        "investors": investors,
        "news": news,
        "jobs": jobs,
        "total_results": total_results
    })

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    print("INDEX SESSION:", dict(request.session))
    db = SessionLocal()
    try:
        # Простые запросы без сервисов
        companies = db.query(Company).filter(Company.status == 'active').order_by(Company.id.desc()).limit(20).all()
        investors = db.query(Investor).filter(Investor.status == 'active').order_by(Investor.id.desc()).limit(20).all()
        news = db.query(News).options(joinedload(News.author)).filter(News.status == 'active').order_by(News.date.desc()).limit(10).all()
        podcasts = db.query(Podcast).filter(Podcast.status == 'active').order_by(Podcast.date.desc()).limit(10).all()
        jobs = db.query(Job).filter(Job.status == 'active').order_by(Job.id.desc()).limit(10).all()
        events = db.query(Event).filter(Event.status == 'active').order_by(Event.date.desc()).limit(10).all()
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
def companies(
    request: Request, 
    q: str = Query('', alias='q'), 
    country: str = Query('', alias='country'), 
    stage: str = Query('', alias='stage'), 
    industry: str = Query('', alias='industry'),
    page: int = Query(1, alias='page'),
    per_page: int = Query(20, alias='per_page')
):
    print("COMPANIES SESSION:", dict(request.session))
    
    # Простая пагинация без сервисов
    per_page = min(per_page, 100)  # Максимум 100
    offset = (page - 1) * per_page
    
    db = SessionLocal()
    try:
        query = db.query(Company).filter(Company.status == 'active')
        if q:
            # Поиск по названию, описанию и индустрии
            from sqlalchemy import or_
            search_filter = or_(
                Company.name.ilike(f'%{q}%'),
                Company.description.ilike(f'%{q}%'),
                Company.industry.ilike(f'%{q}%')
            )
            query = query.filter(search_filter)
        if country:
            query = query.filter_by(country=country)
        if stage:
            query = query.filter_by(stage=stage)
        if industry:
            query = query.filter_by(industry=industry)
        
        # Получаем общее количество
        total = query.count()
        
        # Применяем пагинацию
        companies = query.order_by(Company.name).offset(offset).limit(per_page).all()
        
        # Получаем фильтры
        countries = [c[0] for c in db.query(Company.country).distinct().order_by(Company.country) if c[0]]
        stages = [s[0] for s in db.query(Company.stage).distinct().order_by(Company.stage) if s[0]]
        industries = [i[0] for i in db.query(Company.industry).distinct().order_by(Company.industry) if i[0]]
    finally:
        db.close()
    
    # Простая пагинация
    total_pages = (total + per_page - 1) // per_page
    
    return templates.TemplateResponse("public/companies/list.html", {
        "request": request, 
        "session": request.session, 
        "companies": companies, 
        "countries": countries, 
        "stages": stages, 
        "industries": industries,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None
        },
        "show_per_page_selector": True
    })

@app.get("/company/{id}", response_class=HTMLResponse)
def company_profile(request: Request, id: int = Path(...)):
    db = SessionLocal()
    company = db.query(Company).options(
        joinedload(Company.deals),
        joinedload(Company.pitches),
        joinedload(Company.team),
        joinedload(Company.jobs)
    ).get(id)
    if not company:
        db.close()
        raise HTTPException(status_code=404)
    team = list(company.team)
    # Сортируем сделки по ID в убывающем порядке (новые сначала)
    deals = sorted(company.deals, key=lambda x: x.id, reverse=True)
    jobs = list(company.jobs)
    pitches = list(company.pitches)
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
        {"request": request, "company": company, "team": team, "deals": deals, "jobs": jobs, "pitches": pitches, "investor_dict": investor_dict, "session": request.session, "similar": similar}
    )

@app.get("/investors", response_class=HTMLResponse)
def investors(request: Request, q: str = Query('', alias='q'), country: str = Query('', alias='country'), focus: str = Query('', alias='focus'), stages: str = Query('', alias='stages')):
    db = SessionLocal()
    try:
        query = db.query(Investor).filter(Investor.status == 'active')
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
    from models import Deal
    db = SessionLocal()
    investor = db.query(Investor).get(id)
    
    # Получаем компании из сделок, где участвовал этот инвестор
    portfolio_companies = []
    if investor:
        # Ищем сделки, где имя инвестора упоминается в поле investors
        deals = db.query(Deal).options(joinedload(Deal.company)).all()
        for deal in deals:
            if deal.investors and investor.name in deal.investors and deal.company:
                # Добавляем компанию с информацией о сделке
                company_data = {
                    'company': deal.company,
                    'deal_type': deal.type,
                    'deal_amount': deal.amount,
                    'deal_valuation': deal.valuation,
                    'deal_date': deal.date,
                    'deal_status': deal.status,
                    'company_stage': deal.company.stage if deal.company else None
                }
                portfolio_companies.append(company_data)
        
        # Сортируем по дате сделки (новые сначала)
        portfolio_companies = sorted(portfolio_companies, key=lambda x: x['deal_date'] if x['deal_date'] else datetime.min, reverse=True)
    
    team = list(investor.team) if investor else []
    db.close()
    return templates.TemplateResponse("public/investors/detail.html", {"request": request, "session": request.session, "investor": investor, "portfolio_companies": portfolio_companies, "team": team})

@app.get("/news", response_class=HTMLResponse)
def news_list(request: Request):
    db = SessionLocal()
    news = db.query(News).options(joinedload(News.author)).order_by(News.date.desc()).all()
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
    
    # Увеличиваем счетчик просмотров
    news.views = (news.views or 0) + 1
    db.commit()
    
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
def events_list(request: Request, q: str = Query('', alias='q'), date: str = Query('', alias='date'), format_: str = Query('', alias='format'), country: str = Query('', alias='country')):
    db = SessionLocal()
    query = db.query(Event)
    
    # Фильтр по поиску
    if q:
        query = query.filter(Event.title.ilike(f'%{q}%'))
    
    # Фильтр по дате
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter(Event.date >= filter_date, Event.date < filter_date + timedelta(days=1))
        except ValueError:
            pass
    
    # Фильтр по формату
    if format_:
        query = query.filter(Event.format == format_)
    
    # Фильтр по стране
    if country:
        query = query.filter(Event.country == country)
    
    events = query.order_by(Event.date.asc()).all()
    
    # Получаем уникальные значения для фильтров
    formats = [f[0] for f in db.query(Event.format).distinct().order_by(Event.format) if f[0]]
    # Получаем страны из справочника
    countries = [c.name for c in db.query(Country).filter(Country.status == 'active').order_by(Country.name).all()]
    
    # Маппинг форматов на русские названия
    format_mapping = {
        'online': 'Онлайн',
        'offline': 'Офлайн', 
        'hybrid': 'Гибрид',
        'Online': 'Онлайн',
        'Offline': 'Офлайн',
        'Hybrid': 'Гибрид'
    }
    
    # Преобразуем форматы в русские названия
    formats_russian = []
    for format_item in formats:
        formats_russian.append(format_mapping.get(format_item, format_item))
    
    # Генерируем календарь для фильтрации по дням
    today = datetime.now().date()
    calendar_dates = []
    
    # Генерируем даты на 30 дней вперед
    day_names = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
    for i in range(30):
        date_obj = today + timedelta(days=i)
        day_name = day_names[date_obj.weekday()]
        is_weekend = date_obj.weekday() >= 5  # Суббота и воскресенье
        calendar_dates.append({
            'date': date_obj.strftime('%Y-%m-%d'),
            'day': date_obj.day,
            'day_name': day_name,
            'is_weekend': is_weekend,
            'is_today': date_obj == today
        })
    
    db.close()
    return templates.TemplateResponse("public/events/list.html", {
        "request": request, 
        "session": request.session, 
        "events": events,
        "q": q,
        "date": date,
        "format": format_,
        "country": country,
        "formats": formats_russian,
        "countries": countries,
        "calendar_dates": calendar_dates
    })

@app.get("/event/{id}", response_class=HTMLResponse)
def event_detail(request: Request, id: int = Path(...)):
    db = SessionLocal()
    event = db.query(Event).get(id)
    
    # Получаем другие мероприятия
    other_events = db.query(Event).filter(
        Event.id != id,
        Event.status == 'active'
    ).order_by(Event.date.asc()).limit(5).all()
    
    # Получаем ближайшие новости
    upcoming_news = db.query(News).filter(
        News.status == 'active'
    ).order_by(News.date.desc()).limit(3).all()
    
    db.close()
    return templates.TemplateResponse("public/events/detail.html", {
        "request": request, 
        "session": request.session, 
        "event": event,
        "other_events": other_events,
        "upcoming_news": upcoming_news
    })

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
        company.updated_at = datetime.datetime.utcnow()
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
                user = User(email=email, password=get_password_hash(password), role=role, status=status_val, first_name=first_name, last_name=last_name, country_id=country_id, city=city, phone=phone, telegram=telegram, linkedin=linkedin)
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
        user.password = get_password_hash(form.get('password'))
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
    deals = []
    if company:
        # Сортируем сделки по ID в убывающем порядке (новые сначала)
        sorted_deals = sorted(company.deals, key=lambda x: x.id, reverse=True)
        for deal in sorted_deals:
            deals.append({
                'id': deal.id,
                'type': deal.type,
                'amount': deal.amount,
                'valuation': deal.valuation,
                'investors': deal.investors,
                'date': deal.date,
                'status': deal.status
            })
    jobs = company.jobs if company else []
    db.close()
    return templates.TemplateResponse("admin/companies/form.html", {"request": request, "error": error, "company": company, "team": team, "deals": deals, "jobs": jobs, "countries": countries, "cities": cities})

@app.post("/admin/companies/edit/{company_id}", name="admin_edit_company_post")
async def admin_edit_startup_post(request: Request, company_id: int):
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
    # Обработка даты основания
    founded_date_str = form.get('founded_date')
    if founded_date_str:
        try:
            company.founded_date = datetime.datetime.strptime(founded_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    else:
        company.founded_date = None
    company.updated_at = datetime.datetime.utcnow()
    
    # --- обработка питча ---
    pitch_file = form.get('pitch')
    delete_pitch = form.get('delete_pitch')
    
    if delete_pitch:
        # Удаляем старый файл если есть
        if company.pitch and os.path.exists(company.pitch.lstrip('/')):
            try:
                os.remove(company.pitch.lstrip('/'))
            except:
                pass
        company.pitch = None
        company.pitch_date = None
    elif pitch_file and hasattr(pitch_file, 'filename') and pitch_file.filename:
        # Удаляем старый файл если есть
        if company.pitch and os.path.exists(company.pitch.lstrip('/')):
            try:
                os.remove(company.pitch.lstrip('/'))
            except:
                pass
        
        # Сохраняем новый файл
        filename = f"pitch_{company_id}_{pitch_file.filename}"
        save_dir = os.path.join("static", "pitches")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        contents = await pitch_file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        company.pitch = f"/static/pitches/{filename}"
        
        # Устанавливаем дату питча только если его раньше не было
        if not company.pitch_date:
            company.pitch_date = datetime.datetime.utcnow()
    
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
        description = form.get('description')
        website = form.get('website')
        status = form.get('status')
        db = SessionLocal()
        if db.query(Author).filter_by(name=name).first():
            error = 'Автор с таким именем уже существует'
        else:
            author = Author(
                name=name,
                description=description,
                website=website,
                status=status
            )
            db.add(author)
            db.commit()
            db.close()
            return RedirectResponse(url="/admin/authors", status_code=302)
        db.close()
    return templates.TemplateResponse("admin/authors/form.html", {"request": request, "session": request.session, "error": error, "author": None})

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
    author.description = form.get('description')
    author.website = form.get('website')
    author.status = form.get('status')
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
def admin_jobs(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page'), sort: str = Query('newest', alias='sort')):
    from models import Job, Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Job)
    if q:
        query = query.filter(Job.title.ilike(f'%{q}%'))
    
    # Сортировка
    if sort == 'oldest':
        query = query.order_by(Job.id.asc())
    elif sort == 'name_asc':
        query = query.order_by(Job.title.asc())
    elif sort == 'name_desc':
        query = query.order_by(Job.title.desc())
    elif sort == 'date_asc':
        query = query.order_by(Job.created_at.asc())
    elif sort == 'date_desc':
        query = query.order_by(Job.created_at.desc())
    else:  # newest (по умолчанию)
        query = query.order_by(Job.id.desc())
    
    total = query.count()
    jobs = query.offset((page-1)*per_page).limit(per_page).all()
    companies_list = db.query(Company).all()
    companies = {s.id: s for s in companies_list}
    db.close()
    return templates.TemplateResponse("admin/jobs/list.html", {"request": request, "session": request.session, "jobs": jobs, "q": q, "per_page": per_page, "page": page, "total": total, "companies": companies, "sort": sort})

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

# --- Events CRUD ---
@app.get("/admin/events", response_class=HTMLResponse, name="admin_events")
def admin_events(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page'), sort: str = Query('newest', alias='sort')):
    from models import Event
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Event)
    if q:
        query = query.filter(Event.title.ilike(f'%{q}%'))
    if status:
        query = query.filter(Event.status == status)
    
    # Сортировка
    if sort == 'oldest':
        query = query.order_by(Event.id.asc())
    elif sort == 'name_asc':
        query = query.order_by(Event.title.asc())
    elif sort == 'name_desc':
        query = query.order_by(Event.title.desc())
    elif sort == 'date_asc':
        query = query.order_by(Event.date.asc())
    elif sort == 'date_desc':
        query = query.order_by(Event.date.desc())
    else:  # newest (по умолчанию)
        query = query.order_by(Event.id.desc())
    
    total = query.count()
    events = query.offset((page-1)*per_page).limit(per_page).all()
    response = templates.TemplateResponse("admin/events/list.html", {"request": request, "session": request.session, "events": events, "q": q, "status": status, "per_page": per_page, "page": page, "total": total, "sort": sort})
    db.close()
    return response

@app.route("/admin/events/create", methods=["GET", "POST"], name="admin_create_event")
async def admin_create_event(request: Request):
    from models import Event
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    if request.method == "POST":
        form = await request.form()
        title = form.get('title')
        description = form.get('description')
        date_str = form.get('date')
        format_ = form.get('format')
        location = form.get('location')
        country = form.get('country')
        registration_url = form.get('registration_url')
        status = form.get('status')
        
        # Обработка даты
        try:
            date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') if date_str else None
        except ValueError:
            date = None
        
        # Обработка обложки
        cover_image_path = None
        files = await request.form()
        if 'cover_image' in files:
            cover_file = files['cover_image']
            if cover_file and hasattr(cover_file, 'file') and cover_file.file:
                # Создаем папку для изображений если её нет
                import os
                os.makedirs('static/event_images', exist_ok=True)
                
                # Генерируем уникальное имя файла
                import uuid
                file_extension = os.path.splitext(cover_file.filename)[1] if cover_file.filename else '.jpg'
                filename = f"{uuid.uuid4()}{file_extension}"
                file_path = f"static/event_images/{filename}"
                
                # Сохраняем файл
                with open(file_path, 'wb') as f:
                    content = cover_file.file.read()
                    f.write(content)
                
                cover_image_path = f"/{file_path}"
        
        db = SessionLocal()
        event = Event(
            title=title,
            description=description,
            date=date,
            format=format_,
            location=location,
            country=country,
            registration_url=registration_url,
            cover_image=cover_image_path,
            status=status,
            created_by=request.session.get('user_email', 'admin')
        )
        db.add(event)
        db.commit()
        db.close()
        return RedirectResponse(url="/admin/events", status_code=302)
    
    # Получаем список стран из справочника
    db = SessionLocal()
    countries = db.query(Country).filter(Country.status == 'active').order_by(Country.name).all()
    db.close()
    
    return templates.TemplateResponse("admin/events/form.html", {
        "request": request, 
        "session": request.session, 
        "event": None,
        "countries": countries
    })

@app.get("/admin/events/edit/{event_id}", response_class=HTMLResponse, name="admin_edit_event")
async def admin_edit_event(request: Request, event_id: int):
    from models import Event
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    event = db.query(Event).get(event_id)
    if not event:
        db.close()
        return RedirectResponse(url="/admin/events", status_code=302)
    
    # Получаем список стран из справочника
    countries = db.query(Country).filter(Country.status == 'active').order_by(Country.name).all()
    
    response = templates.TemplateResponse("admin/events/form.html", {
        "request": request, 
        "session": request.session, 
        "event": event,
        "countries": countries
    })
    db.close()
    return response

@app.post("/admin/events/edit/{event_id}", name="admin_edit_event_post")
async def admin_edit_event_post(request: Request, event_id: int):
    from models import Event
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    title = form.get('title')
    description = form.get('description')
    date_str = form.get('date')
    format_ = form.get('format')
    location = form.get('location')
    country = form.get('country')
    registration_url = form.get('registration_url')
    status = form.get('status')
    
    # Обработка даты
    try:
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') if date_str else None
    except ValueError:
        date = None
    
    # Обработка обложки
    cover_image_path = None
    files = await request.form()
    if 'cover_image' in files:
        cover_file = files['cover_image']
        if cover_file and hasattr(cover_file, 'file') and cover_file.file:
            # Создаем папку для изображений если её нет
            import os
            os.makedirs('static/event_images', exist_ok=True)
            
            # Генерируем уникальное имя файла
            import uuid
            file_extension = os.path.splitext(cover_file.filename)[1] if cover_file.filename else '.jpg'
            filename = f"{uuid.uuid4()}{file_extension}"
            file_path = f"static/event_images/{filename}"
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                content = cover_file.file.read()
                f.write(content)
            
            cover_image_path = f"/{file_path}"
    
    db = SessionLocal()
    event = db.query(Event).get(event_id)
    if event:
        event.title = title
        event.description = description
        event.date = date
        event.format = format_
        event.location = location
        event.country = country
        event.registration_url = registration_url
        if cover_image_path:
            event.cover_image = cover_image_path
        event.status = status
        event.updated_by = request.session.get('user_email', 'admin')
        db.commit()
    db.close()
    return RedirectResponse(url="/admin/events", status_code=302)

@app.post("/admin/events/delete/{event_id}", name="admin_delete_event")
async def admin_delete_event(request: Request, event_id: int):
    from models import Event
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    event = db.query(Event).get(event_id)
    db.delete(event)
    db.commit()
    return RedirectResponse(url="/admin/events", status_code=302)

# --- News CRUD ---
@app.get("/admin/news", response_class=HTMLResponse, name="admin_news")
def admin_news(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page'), sort: str = Query('newest', alias='sort')):
    from models import News
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(News).options(joinedload(News.author))
    if q:
        query = query.filter(News.title.ilike(f'%{q}%'))
    
    # Сортировка
    if sort == 'oldest':
        query = query.order_by(News.id.asc())
    elif sort == 'name_asc':
        query = query.order_by(News.title.asc())
    elif sort == 'name_desc':
        query = query.order_by(News.title.desc())
    elif sort == 'date_asc':
        query = query.order_by(News.created_at.asc())
    elif sort == 'date_desc':
        query = query.order_by(News.created_at.desc())
    else:  # newest (по умолчанию)
        query = query.order_by(News.id.desc())
    
    total = query.count()
    news = query.offset((page-1)*per_page).limit(per_page).all()
    response = templates.TemplateResponse("admin/news/list.html", {"request": request, "session": request.session, "news": news, "q": q, "per_page": per_page, "page": page, "total": total, "sort": sort})
    db.close()
    return response

@app.route("/admin/news/create", methods=["GET", "POST"], name="admin_create_news")
async def admin_create_news(request: Request):
    from models import News, Author
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    authors = db.query(Author).filter(Author.status == 'active').all()
    
    error = None
    if request.method == "POST":
        form = await request.form()
        title = form.get('title')
        summary = form.get('summary')
        content = form.get('content')
        date_str = form.get('date')
        status = form.get('status')
        author_id = form.get('author_id')
        
        # Обработка даты
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        except ValueError:
            date = datetime.now().date()
        
        # Обработка author_id
        author_id = int(author_id) if author_id else None
        
        # Валидация длины контента
        if content and len(content) > 5000:
            error = 'Текст новости не может превышать 5000 символов. Текущая длина: {} символов.'.format(len(content))
            db.close()
            return templates.TemplateResponse("admin/news/form.html", {
                "request": request, 
                "session": request.session, 
                "error": error, 
                "success_message": None,
                "news_item": None,
                "authors": authors
            })
        
        # Обработка изображения
        image_path = None
        files = await request.form()
        if 'image' in files:
            image_file = files['image']
            if image_file and hasattr(image_file, 'file') and image_file.file:
                # Создаем папку для изображений если её нет
                import os
                os.makedirs('static/news_images', exist_ok=True)
                
                # Генерируем уникальное имя файла
                import uuid
                file_extension = os.path.splitext(image_file.filename)[1] if image_file.filename else '.jpg'
                filename = f"{uuid.uuid4()}{file_extension}"
                file_path = f"static/news_images/{filename}"
                
                # Сохраняем файл
                with open(file_path, 'wb') as f:
                    content = image_file.file.read()
                    f.write(content)
                
                image_path = f"/{file_path}"
        
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
            summary=summary,
            seo_description=summary,  # Используем summary как SEO описание
            content=content,
            date=date,
            image=image_path,
            status=status,
            author_id=author_id,
            created_by=request.session.get('user_email', 'admin'),
            views=0
        )
        db.add(news)
        db.commit()
        db.close()
        
        # Добавляем уведомление в сессию
        request.session['success_message'] = 'Новость успешно создана!'
        return RedirectResponse(url=f"/admin/news/edit/{news.id}", status_code=302)
    
    db.close()
    return templates.TemplateResponse("admin/news/form.html", {
        "request": request, 
        "session": request.session, 
        "error": error, 
        "success_message": None,
        "news_item": None,
        "authors": authors
    })

@app.get("/admin/news/edit/{news_id}", response_class=HTMLResponse, name="admin_edit_news")
async def admin_edit_news(request: Request, news_id: int):
    from models import News, Author
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    news = db.query(News).get(news_id)
    authors = db.query(Author).filter(Author.status == 'active').all()
    error = None
    
    # Получаем уведомление из сессии
    success_message = request.session.pop('success_message', None)
    
    # Обрабатываем контент новости
    if news and news.content:
        if isinstance(news.content, bytes):
            try:
                news.content = news.content.decode('utf-8')
            except UnicodeDecodeError:
                news.content = ''
        elif not isinstance(news.content, str):
            news.content = str(news.content)
    
    db.close()
    return templates.TemplateResponse("admin/news/form.html", {
        "request": request, 
        "session": request.session, 
        "error": error, 
        "success_message": success_message,
        "news_item": news,
        "authors": authors
    })

@app.post("/admin/news/edit/{news_id}", name="admin_edit_news_post")
async def admin_edit_news_post(request: Request, news_id: int):
    from models import News
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    news = db.query(News).get(news_id)
    form = await request.form()
    
    title = form.get('title')
    summary = form.get('summary')
    content = form.get('content')
    date_str = form.get('date')
    status = form.get('status')
    author_id = form.get('author_id')
    
    # Обработка даты
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
    except ValueError:
        date = datetime.now().date()
    
    # Обработка author_id
    author_id = int(author_id) if author_id else None
    
    # Валидация длины контента
    if content and len(content) > 5000:
        error = 'Текст новости не может превышать 5000 символов. Текущая длина: {} символов.'.format(len(content))
        authors = db.query(Author).filter(Author.status == 'active').all()
        db.close()
        return templates.TemplateResponse("admin/news/form.html", {
            "request": request, 
            "session": request.session, 
            "error": error, 
            "success_message": None,
            "news_item": news,
            "authors": authors
        })
    
    # Обработка изображения
    files = await request.form()
    if 'image' in files:
        image_file = files['image']
        if image_file and hasattr(image_file, 'file') and image_file.file:
            # Создаем папку для изображений если её нет
            import os
            os.makedirs('static/news_images', exist_ok=True)
            
            # Генерируем уникальное имя файла
            import uuid
            file_extension = os.path.splitext(image_file.filename)[1] if image_file.filename else '.jpg'
            filename = f"{uuid.uuid4()}{file_extension}"
            file_path = f"static/news_images/{filename}"
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                image_content = image_file.file.read()
                f.write(image_content)
            
            # Удаляем старое изображение если есть
            if news.image and os.path.exists(news.image.lstrip('/')):
                try:
                    os.remove(news.image.lstrip('/'))
                except:
                    pass
            
            news.image = f"/{file_path}"
    
    # Обновляем поля
    news.title = title
    news.summary = summary
    news.seo_description = summary  # Используем summary как SEO описание
    news.content = content
    news.date = date
    news.status = status
    news.author_id = author_id
    news.updated_by = request.session.get('user_email', 'admin')
    
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
    
    # Добавляем уведомление в сессию
    request.session['success_message'] = 'Новость успешно обновлена!'
    return RedirectResponse(url=f"/admin/news/edit/{news_id}", status_code=302)

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



@app.get("/admin/investors", response_class=HTMLResponse, name="admin_investors")
async def admin_investors(request: Request, q: str = Query('', alias='q'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page'), sort: str = Query('newest', alias='sort')):
    from models import Investor
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Investor)
    if q:
        query = query.filter(Investor.name.ilike(f'%{q}%'))
    
    # Сортировка
    if sort == 'oldest':
        query = query.order_by(Investor.id.asc())
    elif sort == 'name_asc':
        query = query.order_by(Investor.name.asc())
    elif sort == 'name_desc':
        query = query.order_by(Investor.name.desc())
    elif sort == 'date_asc':
        query = query.order_by(Investor.created_at.asc())
    elif sort == 'date_desc':
        query = query.order_by(Investor.created_at.desc())
    else:  # newest (по умолчанию)
        query = query.order_by(Investor.id.desc())
    
    total = query.count()
    investors = query.offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/investors/list.html", {"request": request, "session": request.session, "investors": investors, "q": q, "per_page": per_page, "page": page, "total": total, "sort": sort})

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
    from models import Investor, PortfolioEntry
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
    # Получаем сделки, где участвовал этот инвестор
    portfolio_deals = []
    if investor:
        from models import Deal
        # Ищем сделки, где имя инвестора упоминается в поле investors
        deals = db.query(Deal).options(joinedload(Deal.company)).all()
        for deal in deals:
            if deal.investors and investor.name in deal.investors:
                portfolio_deals.append(deal)
        # Сортируем по ID в убывающем порядке (новые сначала)
        portfolio_deals = sorted(portfolio_deals, key=lambda x: x.id, reverse=True)
    
    response = templates.TemplateResponse("admin/investors/form.html", {"request": request, "session": request.session, "investor": investor, "portfolio_entries": investor.portfolio_entries if investor else [], "portfolio_deals": portfolio_deals, "error": error, "today": today})
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

# === Админ панель: Портфель инвестора ===

@app.post("/admin/investors/{investor_id}/portfolio/entry/add", name="admin_add_portfolio_entry")
async def admin_add_portfolio_entry(request: Request, investor_id: int):
    from fastapi.responses import JSONResponse
    from models import Investor, PortfolioEntry, Company
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    company_id = form.get('company_id')
    amount = form.get('amount')
    valuation = form.get('valuation')
    date_str = form.get('date')
    
    if not company_id or not amount or not date_str:
        return JSONResponse({"error": "Заполните все обязательные поля"})
    
    db = SessionLocal()
    try:
        # Проверяем существование инвестора и компании
        investor = db.query(Investor).get(investor_id)
        company = db.query(Company).get(company_id)
        
        if not investor or not company:
            return JSONResponse({"error": "Инвестор или компания не найдены"})
        
        # Обработка даты
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return JSONResponse({"error": "Неверный формат даты"})
        
        # Создаем запись в портфеле
        portfolio_entry = PortfolioEntry(
            investor_id=investor_id,
            company_id=int(company_id),
            amount=float(amount) if amount else None,
            valuation=float(valuation) if valuation else None,
            date=date
        )
        db.add(portfolio_entry)
        db.commit()
        
        return JSONResponse({"success": True, "message": "Запись добавлена в портфель"})
        
    except Exception as e:
        db.rollback()
        return JSONResponse({"error": f"Ошибка при добавлении записи: {str(e)}"})
    finally:
        db.close()

@app.post("/admin/investors/{investor_id}/portfolio/entry/delete/{entry_id}", name="admin_delete_portfolio_entry")
async def admin_delete_portfolio_entry(request: Request, investor_id: int, entry_id: int):
    from models import PortfolioEntry
    from fastapi.responses import JSONResponse
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    try:
        entry = db.query(PortfolioEntry).filter(
            PortfolioEntry.id == entry_id,
            PortfolioEntry.investor_id == investor_id
        ).first()
        
        if entry:
            db.delete(entry)
            db.commit()
            return JSONResponse({"success": True, "message": "Запись удалена из портфеля"})
        else:
            return JSONResponse({"error": "Запись не найдена"})
            
    except Exception as e:
        db.rollback()
        return JSONResponse({"error": f"Ошибка при удалении записи: {str(e)}"})
    finally:
        db.close()

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
@app.get("/admin/team/create", name="admin_create_team_member_form")
async def admin_create_team_member_form(request: Request):
    from models import Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    # Получаем компанию из query параметра
    company_id = request.query_params.get('company_id')
    if not company_id:
        return RedirectResponse(url="/admin/companies", status_code=302)
    
    db = SessionLocal()
    try:
        company = db.query(Company).get(int(company_id))
        if not company:
            return RedirectResponse(url="/admin/companies", status_code=302)
        
        return templates.TemplateResponse("admin/team/create.html", {
            "request": request, 
            "company": company
        })
    finally:
        db.close()

@app.post("/admin/team/create", name="admin_create_team_member")
async def admin_create_team_member(request: Request):
    from models import Person, Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    form = await request.form()
    name = form.get('name')
    role = form.get('role')
    linkedin = form.get('linkedin')
    telegram = form.get('telegram')
    website = form.get('website')
    instagram = form.get('instagram')
    company_id = int(request.query_params.get('company_id')) if request.query_params.get('company_id') else None
    db = SessionLocal()
    person = Person(name=name, role=role, linkedin=linkedin, telegram=telegram, website=website, instagram=instagram)
    db.add(person)
    db.commit()
    if company_id:
        company = db.query(Company).get(company_id)
        if company:
            company.team.append(person)
            db.commit()
    db.close()
    return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab=team&message=Участник команды успешно добавлен", status_code=302)

@app.get("/admin/team/{person_id}/edit", name="admin_edit_team_member_form")
async def admin_edit_team_member_form(request: Request, person_id: int):
    from models import Person
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    try:
        person = db.query(Person).get(person_id)
        if not person:
            return RedirectResponse(url="/admin/companies", status_code=302)
        
        # Получаем компанию из query параметра
        company_id = request.query_params.get('company_id')
        if not company_id:
            return RedirectResponse(url="/admin/companies", status_code=302)
        
        company = db.query(Company).get(int(company_id))
        if not company:
            return RedirectResponse(url="/admin/companies", status_code=302)
        
        return templates.TemplateResponse("admin/team/edit.html", {
            "request": request, 
            "person": person, 
            "company": company
        })
    finally:
        db.close()

@app.post("/admin/team/{person_id}/edit", name="admin_edit_team_member")
async def admin_edit_team_member(request: Request, person_id: int):
    from models import Person
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    name = form.get('name')
    role = form.get('role')
    linkedin = form.get('linkedin')
    telegram = form.get('telegram')
    website = form.get('website')
    instagram = form.get('instagram')
    company_id = form.get('company_id')
    
    db = SessionLocal()
    try:
        person = db.query(Person).get(person_id)
        if person:
            person.name = name
            person.role = role
            person.linkedin = linkedin
            person.telegram = telegram
            person.website = website
            person.instagram = instagram
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
    
    return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab=team&message=Участник команды успешно обновлен", status_code=302)

@app.post("/admin/team/{person_id}/delete", name="admin_delete_team_member")
async def admin_delete_team_member(request: Request, person_id: int):
    from models import Person, Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    company_id = request.query_params.get('company_id')
    
    db = SessionLocal()
    try:
        person = db.query(Person).get(person_id)
        if person:
            # Удаляем связь с компанией
            for company in person.companies:
                company.team.remove(person)
            # Удаляем самого человека
            db.delete(person)
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
    
    return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab=team&message=Участник команды успешно удален", status_code=302)

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
            admin_user = User(email="admin@stanbase.test", password=get_password_hash("admin123"), role="admin", first_name="Admin", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234567", status="active")
            session.add(admin_user)
            session.commit()
        if not session.query(User).filter_by(email="moderator@stanbase.test").first():
            print(f"Создаём moderator с country_id={kz_id}")
            moderator_user = User(email="moderator@stanbase.test", password=get_password_hash("mod123"), role="moderator", first_name="Mod", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234568", status="active")
            session.add(moderator_user)
            session.commit()
        if not session.query(User).filter_by(email="startuper@stanbase.test").first():
            companies = session.query(Company).all()
            if companies:
                print(f"Создаём startuper с country_id={kz_id}")
                startuper_user = User(email="startuper@stanbase.test", password=get_password_hash("startuper123"), role="startuper", first_name="Start", last_name="Stanbase", country_id=kz_id, city="Алматы", phone="+77001234569", company_id=companies[0].id, status="active")
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

@router.get("/run-migration")
def run_migration():
    """Выполняет миграцию для добавления недостающих колонок"""
    db = SessionLocal()
    try:
        # SQL команды для миграции
        migrations = [
            # Person table
            "ALTER TABLE person ADD COLUMN IF NOT EXISTS telegram VARCHAR(256)",
            "ALTER TABLE person ADD COLUMN IF NOT EXISTS instagram VARCHAR(256)",
            
            # News table
            "ALTER TABLE news ADD COLUMN IF NOT EXISTS slug VARCHAR(256)",
            "ALTER TABLE news ADD COLUMN IF NOT EXISTS seo_description VARCHAR(512)",
            "ALTER TABLE news ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
            "ALTER TABLE news ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
            "ALTER TABLE news ADD COLUMN IF NOT EXISTS created_by VARCHAR(64)",
            "ALTER TABLE news ADD COLUMN IF NOT EXISTS updated_by VARCHAR(64)",
            
            # Event table
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS country VARCHAR(64)",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS cover_image VARCHAR(256)",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS created_by VARCHAR(64)",
            "ALTER TABLE event ADD COLUMN IF NOT EXISTS updated_by VARCHAR(64)",
            
            # Deal table
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS company_id INTEGER",
            "ALTER TABLE deal ADD COLUMN IF NOT EXISTS valuation FLOAT",
            
            # Company table
            "ALTER TABLE company ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
            "ALTER TABLE company ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
            "ALTER TABLE company ADD COLUMN IF NOT EXISTS created_by VARCHAR(64)",
            
            # Investor table
            "ALTER TABLE investor ADD COLUMN IF NOT EXISTS logo VARCHAR(256)",
            
            # User table
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS created_by VARCHAR(64)',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS updated_by VARCHAR(64)',
        ]
        
        executed_migrations = []
        for migration in migrations:
            try:
                db.execute(migration)
                executed_migrations.append(migration)
                print(f"Выполнена миграция: {migration}")
            except Exception as e:
                print(f"Ошибка миграции: {migration} - {e}")
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Миграция завершена. Выполнено {len(executed_migrations)} команд.",
            "executed_migrations": executed_migrations
        }
        
    except Exception as e:
        db.rollback()
        print(f"Ошибка при миграции: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

app.include_router(router)
app.include_router(api_router)



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
async def admin_companies(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page'), sort: str = Query('newest', alias='sort')):
    from models import Company
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    db = SessionLocal()
    query = db.query(Company)
    if q:
        query = query.filter(Company.name.ilike(f'%{q}%'))
    if status:
        query = query.filter(Company.status == status)
    
    # Сортировка
    if sort == 'oldest':
        query = query.order_by(Company.id.asc())
    elif sort == 'name_asc':
        query = query.order_by(Company.name.asc())
    elif sort == 'name_desc':
        query = query.order_by(Company.name.desc())
    else:  # newest (по умолчанию)
        query = query.order_by(Company.id.desc())
    
    total = query.count()
    companies = query.offset((page-1)*per_page).limit(per_page).all()
    db.close()
    return templates.TemplateResponse("admin/companies/list.html", {"request": request, "companies": companies, "q": q, "status": status, "per_page": per_page, "page": page, "total": total, "sort": sort})

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
    from models import Company, Country, City, Deal
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
    pitches = company.pitches if company else []
    deals = db.query(Deal).filter(Deal.company_id == company_id).all() if company else []
    # Преобразуем в список, чтобы избежать проблем с lazy loading
    deals_list = []
    for deal in deals:
        deals_list.append({
            'id': deal.id,
            'type': deal.type,
            'amount': deal.amount,
            'investors': deal.investors,
            'date': deal.date,
            'status': deal.status
        })
    db.close()
    return templates.TemplateResponse("admin/companies/form.html", {"request": request, "company": company, "countries": countries, "cities": cities, "error": error, "team": team, "jobs": jobs, "pitches": pitches, "deals": deals_list})

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
    # Обработка даты основания
    founded_date_str = form.get('founded_date')
    if founded_date_str:
        try:
            company.founded_date = datetime.datetime.strptime(founded_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    else:
        company.founded_date = None
    company.updated_at = datetime.datetime.utcnow()
    
    # --- обработка питча ---
    pitch_file = form.get('pitch')
    delete_pitch = form.get('delete_pitch')
    
    if delete_pitch:
        # Удаляем старый файл если есть
        if company.pitch and os.path.exists(company.pitch.lstrip('/')):
            try:
                os.remove(company.pitch.lstrip('/'))
            except:
                pass
        company.pitch = None
        company.pitch_date = None
    elif pitch_file and hasattr(pitch_file, 'filename') and pitch_file.filename:
        # Удаляем старый файл если есть
        if company.pitch and os.path.exists(company.pitch.lstrip('/')):
            try:
                os.remove(company.pitch.lstrip('/'))
            except:
                pass
        
        # Сохраняем новый файл
        filename = f"pitch_{company_id}_{pitch_file.filename}"
        save_dir = os.path.join("static", "pitches")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        contents = await pitch_file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        company.pitch = f"/static/pitches/{filename}"
        
        # Устанавливаем дату питча только если его раньше не было
        if not company.pitch_date:
            company.pitch_date = datetime.datetime.utcnow()
    
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

# CRUD операции для питчей
@app.post("/admin/pitch/create", name="admin_create_pitch")
async def admin_create_pitch(request: Request):
    from models import Pitch, Company
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    # Получаем company_id из query параметров
    company_id = request.query_params.get('company_id')
    name = form.get('name')
    url = form.get('url')
    status = form.get('status', 'active')
    
    if not company_id:
        return RedirectResponse(url="/admin/companies?error=ID компании не указан", status_code=302)
    
    if not url:
        return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab=pitch&error=URL питча не указан", status_code=302)
    
    db = SessionLocal()
    try:
        # Проверяем существование компании
        company = db.query(Company).get(company_id)
        if not company:
            return RedirectResponse(url="/admin/companies?error=Компания не найдена", status_code=302)
        
        # Создаем запись в БД
        pitch = Pitch(
            name=name,
            url=url,
            status=status,
            company_id=company_id,
            created_by=request.session.get('user_email', 'admin')
        )
        db.add(pitch)
        db.commit()
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab=pitch&error=Ошибка при создании питча", status_code=302)
    finally:
        db.close()
    
    return RedirectResponse(url=f"/admin/companies/edit/{company_id}?tab=pitch", status_code=302)

@app.post("/admin/pitch/{pitch_id}/status", name="admin_update_pitch_status")
async def admin_update_pitch_status(request: Request, pitch_id: int):
    from models import Pitch
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    status = form.get('status')
    
    db = SessionLocal()
    try:
        pitch = db.query(Pitch).get(pitch_id)
        if pitch:
            pitch.status = status
            pitch.updated_at = datetime.datetime.utcnow()
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
    
    return Response(status_code=200)

@app.post("/admin/pitch/{pitch_id}/delete", name="admin_delete_pitch")
async def admin_delete_pitch(request: Request, pitch_id: int):
    from models import Pitch
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    try:
        pitch = db.query(Pitch).get(pitch_id)
        if pitch:
            # Удаляем запись из БД
            db.delete(pitch)
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
    
    return Response(status_code=200)

# CRUD операции для сделок
@app.get("/admin/deals/create", name="admin_create_deal_form")
async def admin_create_deal_form(request: Request):
    from models import CompanyStage, Company, Investor
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    company_id = request.query_params.get('company_id')
    
    db = SessionLocal()
    stages = db.query(CompanyStage).filter(CompanyStage.status == 'active').all()
    companies = db.query(Company).filter(Company.status == 'active').order_by(Company.name).all()
    investors = db.query(Investor).filter(Investor.status == 'active').order_by(Investor.name).all()
    db.close()
    
    return templates.TemplateResponse("admin/deals/create.html", {
        "request": request, 
        "company_id": company_id,
        "stages": stages,
        "companies": companies,
        "investors": investors
    })

@app.post("/admin/deals/create", name="admin_create_deal")
async def admin_create_deal(request: Request):
    from models import Deal, Company
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    company_id = form.get('company_id')
    deal_type = form.get('deal_type')
    amount = form.get('amount')
    valuation = form.get('valuation')
    investors_list = form.getlist('investors')
    investors = ', '.join(investors_list) if investors_list else ''
    deal_date_str = form.get('deal_date')
    status = form.get('status', 'active')
    
    if not company_id:
        return RedirectResponse(url="/admin/deals/create?error=Выберите компанию", status_code=302)
    
    if not deal_type or not amount:
        return RedirectResponse(url=f"/admin/deals/create?company_id={company_id}&error=Заполните все обязательные поля", status_code=302)
    
    db = SessionLocal()
    try:
        # Проверяем существование компании
        company = db.query(Company).get(company_id)
        if not company:
            return RedirectResponse(url="/admin/companies?error=Компания не найдена", status_code=302)
        
        # Обработка даты
        deal_date = None
        if deal_date_str:
            try:
                deal_date = datetime.datetime.strptime(deal_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # Создаем запись в БД
        deal = Deal(
            type=deal_type,
            amount=float(amount) if amount else None,
            valuation=float(valuation) if valuation else None,
            investors=investors,
            date=deal_date,
            status=status,
            company_id=int(company_id)
        )
        db.add(deal)
        db.commit()
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"/admin/deals/create?company_id={company_id}&error=Ошибка при создании сделки", status_code=302)
    finally:
        db.close()
    
    return RedirectResponse(url=f"/admin/deals?message=Сделка успешно добавлена", status_code=302)

@app.get("/admin/deals/{deal_id}/edit", name="admin_edit_deal_form")
async def admin_edit_deal_form(request: Request, deal_id: int):
    from models import Deal, CompanyStage, Investor
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    deal = db.query(Deal).options(joinedload(Deal.company)).get(deal_id)
    stages = db.query(CompanyStage).filter(CompanyStage.status == 'active').all()
    investors = db.query(Investor).filter(Investor.status == 'active').order_by(Investor.name).all()
    db.close()
    
    if not deal:
        return RedirectResponse(url="/admin/deals?error=Сделка не найдена", status_code=302)
    
    return templates.TemplateResponse("admin/deals/edit.html", {
        "request": request, 
        "deal": deal,
        "stages": stages,
        "investors": investors
    })

@app.post("/admin/deals/{deal_id}/edit", name="admin_edit_deal")
async def admin_edit_deal(request: Request, deal_id: int):
    from models import Deal
    import datetime
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    deal_type = form.get('deal_type')
    amount = form.get('amount')
    valuation = form.get('valuation')
    investors_list = form.getlist('investors')
    investors = ', '.join(investors_list) if investors_list else ''

    deal_date_str = form.get('deal_date')
    status = form.get('status', 'active')
    
    if not deal_type or not amount:
        return RedirectResponse(url=f"/admin/deals/{deal_id}/edit?error=Заполните все обязательные поля", status_code=302)
    
    db = SessionLocal()
    try:
        deal = db.query(Deal).get(deal_id)
        if not deal:
            return RedirectResponse(url="/admin/deals?error=Сделка не найдена", status_code=302)
        
        # Обработка даты
        deal_date = None
        if deal_date_str:
            try:
                deal_date = datetime.datetime.strptime(deal_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # Обновляем запись
        deal.type = deal_type
        deal.amount = float(amount) if amount else None
        deal.valuation = float(valuation) if valuation else None
        deal.investors = investors
        deal.date = deal_date
        deal.status = status
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"/admin/deals/{deal_id}/edit?error=Ошибка при обновлении сделки", status_code=302)
    finally:
        db.close()
    
    return RedirectResponse(url="/admin/deals?message=Сделка успешно обновлена", status_code=302)

@app.post("/admin/deals/{deal_id}/delete", name="admin_delete_deal")
async def admin_delete_deal(request: Request, deal_id: int):
    from models import Deal
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    try:
        deal = db.query(Deal).get(deal_id)
        if deal:
            db.delete(deal)
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
    
    return RedirectResponse(url=f"/admin/deals?message=Сделка успешно удалена", status_code=302)

# === Уведомления ===

@app.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request):
    """Страница уведомлений"""
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)
    
    user_id = request.session.get("user_id")
    notifications = NotificationService.get_user_notifications(user_id, limit=50)
    unread_count = NotificationService.get_unread_count(user_id)
    
    return templates.TemplateResponse("notifications/list.html", {
        "request": request,
        "notifications": notifications,
        "unread_count": unread_count,
        "session": request.session
    })

@app.post("/notifications/{notification_id}/read")
async def mark_notification_read_web(request: Request, notification_id: int):
    """Отметить уведомление как прочитанное (веб)"""
    if not request.session.get("user_id"):
        return JSONResponse({"success": False, "error": "Не авторизован"})
    
    user_id = request.session.get("user_id")
    success = NotificationService.mark_as_read(notification_id, user_id)
    
    return JSONResponse({"success": success})

@app.post("/notifications/read-all")
async def mark_all_notifications_read_web(request: Request):
    """Отметить все уведомления как прочитанные (веб)"""
    if not request.session.get("user_id"):
        return JSONResponse({"success": False, "error": "Не авторизован"})
    
    user_id = request.session.get("user_id")
    count = NotificationService.mark_all_as_read(user_id)
    
    return JSONResponse({"success": True, "count": count})

# === Комментарии ===

@app.post("/comments/add")
async def add_comment(request: Request):
    """Добавить комментарий"""
    if not request.session.get("user_id"):
        return JSONResponse({"success": False, "error": "Не авторизован"})
    
    form = await request.form()
    entity_type = form.get("entity_type")
    entity_id = int(form.get("entity_id"))
    content = form.get("content", "").strip()
    parent_id = form.get("parent_id")
    
    if parent_id:
        parent_id = int(parent_id)
    
    # Валидация
    if not CommentValidator.is_valid_entity_type(entity_type):
        return JSONResponse({"success": False, "error": "Неверный тип сущности"})
    
    validation_errors = CommentValidator.validate_content(content)
    if validation_errors:
        return JSONResponse({"success": False, "error": f"Ошибки валидации: {validation_errors}"})
    
    # Создание комментария
    user_id = request.session.get("user_id")
    comment = CommentService.create_comment(
        user_id=user_id,
        content=content,
        entity_type=entity_type,
        entity_id=entity_id,
        parent_id=parent_id
    )
    
    return JSONResponse({
        "success": True,
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "user_name": f"{comment.user.first_name} {comment.user.last_name}",
            "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M")
        }
    })

@app.get("/comments/{entity_type}/{entity_id}")
async def get_comments_web(request: Request, entity_type: str, entity_id: int):
    """Получить комментарии для сущности (веб)"""
    if not CommentValidator.is_valid_entity_type(entity_type):
        return JSONResponse({"success": False, "error": "Неверный тип сущности"})
    
    comments = CommentService.get_comments(entity_type, entity_id, limit=50)
    
    result = []
    for comment in comments:
        replies = CommentService.get_replies(comment.id)
        result.append({
            "id": comment.id,
            "content": comment.content,
            "user_name": f"{comment.user.first_name} {comment.user.last_name}",
            "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M"),
            "replies": [
                {
                    "id": reply.id,
                    "content": reply.content,
                    "user_name": f"{reply.user.first_name} {reply.user.last_name}",
                    "created_at": reply.created_at.strftime("%d.%m.%Y %H:%M")
                }
                for reply in replies
            ]
        })
    
    return JSONResponse({
        "success": True,
        "comments": result,
        "total": CommentService.get_comment_count(entity_type, entity_id)
    })

@app.get("/admin/deals", response_class=HTMLResponse, name="admin_deals")
async def admin_deals(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    from models import Deal, Company
    from sqlalchemy import or_
    from sqlalchemy.orm import joinedload
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    
    # Базовый запрос с eager loading
    query = db.query(Deal).options(joinedload(Deal.company))
    
    # Поиск
    if q:
        query = query.join(Company).filter(
            or_(
                Deal.type.contains(q),
                Deal.status.contains(q),
                Company.name.contains(q)
            )
        )
    
    # Фильтр по статусу
    if status:
        query = query.filter(Deal.status == status)
    
    # Общее количество
    total = query.count()
    
    # Пагинация
    deals = query.order_by(Deal.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    db.close()
    
    return templates.TemplateResponse("admin/deals/list.html", {
        "request": request,
        "deals": deals,
        "q": q,
        "status": status,
        "page": page,
        "per_page": per_page,
        "total": total
    })

# === Админ панель: Системное - Обратная связь ===

@app.get("/admin/feedback", response_class=HTMLResponse, name="admin_feedback")
async def admin_feedback(request: Request, q: str = Query('', alias='q'), status: str = Query('', alias='status'), per_page: int = Query(10, alias='per_page'), page: int = Query(1, alias='page')):
    """Список обратной связи"""
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    
    # Базовый запрос
    query = db.query(Feedback)
    
    # Фильтрация по поиску
    if q:
        query = query.filter(
            or_(
                Feedback.description.contains(q),
                Feedback.suggestion.contains(q),
                Feedback.name.contains(q),
                Feedback.email.contains(q),
                Feedback.type.contains(q)
            )
        )
    
    # Фильтрация по статусу
    if status:
        query = query.filter(Feedback.status == status)
    
    # Сортировка по ID (новые записи сначала)
    query = query.order_by(Feedback.id.desc())
    
    # Общее количество
    total = query.count()
    
    # Пагинация
    feedback_list = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Подсчет страниц
    total_pages = (total + per_page - 1) // per_page
    
    db.close()
    
    return templates.TemplateResponse("admin/feedback/list.html", {
        "request": request,
        "feedback_list": feedback_list,
        "q": q,
        "status": status,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages
    })

@app.get("/admin/feedback/{feedback_id}/edit", response_class=HTMLResponse, name="admin_feedback_edit")
async def admin_feedback_edit(request: Request, feedback_id: int):
    """Редактирование обратной связи"""
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    db.close()
    
    if not feedback:
        return RedirectResponse(url="/admin/feedback", status_code=302)
    
    return templates.TemplateResponse("admin/feedback/edit.html", {
        "request": request,
        "feedback": feedback
    })

@app.post("/admin/feedback/{feedback_id}/status", name="admin_feedback_status")
async def admin_feedback_status(request: Request, feedback_id: int):
    """Обновить статус обратной связи"""
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    form = await request.form()
    new_status = form.get('status')
    admin_notes = form.get('admin_notes', '')
    
    if new_status not in ['new', 'in_progress', 'resolved', 'closed']:
        return RedirectResponse(url=f"/admin/feedback/{feedback_id}/edit", status_code=302)
    
    db = SessionLocal()
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if feedback:
        feedback.status = new_status
        feedback.admin_notes = admin_notes
        feedback.processed_by = request.session.get('user_name', 'Admin')
        feedback.processed_at = datetime.utcnow()
        feedback.updated_at = datetime.utcnow()
        db.commit()
    
    db.close()
    
    return RedirectResponse(url=f"/admin/feedback/{feedback_id}/edit", status_code=302)

@app.post("/admin/feedback/{feedback_id}/delete", name="admin_feedback_delete")
async def admin_feedback_delete(request: Request, feedback_id: int):
    """Удалить обратную связь"""
    if not admin_required(request):
        return RedirectResponse(url="/login", status_code=302)
    
    db = SessionLocal()
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if feedback:
        db.delete(feedback)
        db.commit()
    
    db.close()
    
    return RedirectResponse(url="/admin/feedback", status_code=302)

# === Страницы политики и условий ===

@app.get("/privacy", response_class=HTMLResponse)
def privacy_page(request: Request):
    """Страница политики конфиденциальности"""
    return templates.TemplateResponse("public/privacy.html", {
        "request": request,
        "session": request.session
    })

@app.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request):
    """Страница условий использования"""
    return templates.TemplateResponse("public/terms.html", {
        "request": request,
        "session": request.session
    })



if __name__ == "__main__":
    print('SERVER STARTED')
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 