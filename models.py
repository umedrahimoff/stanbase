from db import Base
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, backref
from datetime import datetime

company_person = Table('company_person', Base.metadata,
    Column('company_id', Integer, ForeignKey('company.id')),
    Column('person_id', Integer, ForeignKey('person.id'))
)

investor_company = Table('investor_company', Base.metadata,
    Column('investor_id', Integer, ForeignKey('investor.id')),
    Column('company_id', Integer, ForeignKey('company.id'))
)

investor_person = Table('investor_person', Base.metadata,
    Column('investor_id', Integer, ForeignKey('investor.id')),
    Column('person_id', Integer, ForeignKey('person.id'))
)

class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    country = Column(String(64))
    city = Column(String(64))
    stage = Column(String(32))
    industry = Column(String(64))
    founded_date = Column(Date)
    website = Column(String(256))
    logo = Column(String(256), nullable=True)  # путь к файлу логотипа
    team = relationship('Person', secondary=company_person, backref='companies')
    pitches = relationship('Pitch', backref='company', cascade='all, delete-orphan')
    deals = relationship('Deal', backref='company', cascade='all, delete-orphan')
    jobs = relationship('Job', backref='company', cascade='all, delete-orphan')
    users = relationship('User', backref='company', cascade='all, delete-orphan')
    status = Column(String(16), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(64))

class PortfolioEntry(Base):
    __tablename__ = 'portfolio_entry'
    id = Column(Integer, primary_key=True)
    investor_id = Column(Integer, ForeignKey('investor.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    valuation = Column(Float, nullable=True)
    investor = relationship('Investor', back_populates='portfolio_entries')
    company = relationship('Company')

class Investor(Base):
    __tablename__ = 'investor'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    country = Column(String(64))
    focus = Column(String(128))
    stages = Column(String(128))
    portfolio = relationship('Company', secondary=investor_company, backref='investors')
    portfolio_entries = relationship('PortfolioEntry', back_populates='investor', cascade='all, delete-orphan')
    team = relationship('Person', secondary=investor_person, backref='investor_teams')
    website = Column(String(256))
    status = Column(String(16), default='active')
    type = Column(String(16), default='angel')
    logo = Column(String(256), nullable=True)  # путь к файлу логотипа

class Deal(Base):
    __tablename__ = 'deal'
    id = Column(Integer, primary_key=True)
    type = Column(String(32))
    amount = Column(Float)
    valuation = Column(Float, nullable=True)
    date = Column(Date)
    company_id = Column(Integer, ForeignKey('company.id'))
    investors = Column(String(256))
    status = Column(String(16), default='active')

class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    country = Column(String(64))
    linkedin = Column(String(256))
    telegram = Column(String(256))
    website = Column(String(256))
    instagram = Column(String(256))
    role = Column(String(64))
    status = Column(String(16), default='active')

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    slug = Column(String(256), unique=True, nullable=True)
    summary = Column(String(512))
    seo_description = Column(String(512))  # SEO описание для meta description
    date = Column(Date, default=datetime.utcnow)
    content = Column(Text)
    image = Column(String(256), nullable=True)  # путь к изображению новости
    views = Column(Integer, default=0)
    status = Column(String(16), default='active')
    author_id = Column(Integer, ForeignKey('author.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(64), nullable=True)
    updated_by = Column(String(64), nullable=True)

class Podcast(Base):
    __tablename__ = 'podcast'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    description = Column(Text)
    youtube_url = Column(String(256))
    date = Column(Date, default=datetime.utcnow)
    status = Column(String(16), default='active')

class Job(Base):
    __tablename__ = 'job'
    id = Column(Integer, primary_key=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    company_id = Column(Integer, ForeignKey('company.id'))
    city = Column(String(64))
    job_type = Column(String(32))
    contact = Column(String(128))
    status = Column(String(16), default='active')

class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    description = Column(Text)
    date = Column(DateTime)
    format = Column(String(32))
    location = Column(String(128))
    country = Column(String(64), nullable=True)  # страна проведения мероприятия
    registration_url = Column(String(256))
    cover_image = Column(String(256), nullable=True)  # путь к обложке мероприятия
    status = Column(String(16), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(64), nullable=True)
    updated_by = Column(String(64), nullable=True)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(128), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Увеличиваем для хешированных паролей
    role = Column(String(32), nullable=False)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    city = Column(String(64), nullable=False)
    phone = Column(String(32), nullable=False)
    telegram = Column(String(64), nullable=True)
    linkedin = Column(String(256), nullable=True)
    investor_id = Column(Integer, ForeignKey('investor.id'), nullable=True)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=True)
    status = Column(String(16), default='active')
    country = relationship('Country', backref='users')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(64), nullable=True)
    updated_by = Column(String(64), nullable=True)

class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    status = Column(String(16), default='active')
    cities = relationship('City', backref='country', lazy=True)

class City(Base):
    __tablename__ = 'city'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    status = Column(String(16), default='active')

class CompanyStage(Base):
    __tablename__ = 'company_stage'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, nullable=False)
    status = Column(String(16), default='active')

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    status = Column(String(16), default='active')

class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    website = Column(String(256))
    status = Column(String(16), default='active')
    news = relationship('News', backref='author')



class Pitch(Base):
    __tablename__ = 'pitch'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)  # название питча
    url = Column(String(512), nullable=False)  # ссылка на питч
    status = Column(String(16), default='active')  # active, inactive, archived, draft
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(64), nullable=True)

class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    entity_type = Column(String(32), nullable=False)  # 'company', 'investor', 'news', 'job'
    entity_id = Column(Integer, nullable=False)
    parent_id = Column(Integer, ForeignKey('comment.id'), nullable=True)  # для ответов
    status = Column(String(16), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    user = relationship('User', backref='comments')
    replies = relationship('Comment', backref=backref('parent', remote_side=[id]))

class Notification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(32), nullable=False)  # 'info', 'success', 'warning', 'error'
    entity_type = Column(String(32), nullable=True)  # 'company', 'investor', 'news', 'job'
    entity_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship('User', backref='notifications')

class UserActivity(Base):
    __tablename__ = 'user_activity'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    action = Column(String(64), nullable=False)  # 'login', 'logout', 'create', 'update', 'delete'
    entity_type = Column(String(32), nullable=True)
    entity_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship('User', backref='activities')

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    type = Column(String(32), nullable=False)  # 'bug', 'feature', 'improvement', 'other'
    description = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    name = Column(String(128), nullable=True)
    email = Column(String(128), nullable=True)
    
    # Техническая информация
    page_url = Column(String(512), nullable=True)
    page_title = Column(String(256), nullable=True)
    user_agent = Column(String(512), nullable=True)
    screen_size = Column(String(64), nullable=True)
    is_authenticated = Column(Boolean, default=False)
    
    # Статус обработки
    status = Column(String(16), default='new')  # 'new', 'in_progress', 'resolved', 'closed'
    admin_notes = Column(Text, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = Column(String(64), nullable=True)
    processed_at = Column(DateTime, nullable=True)

class EmailTemplate(Base):
    __tablename__ = 'email_template'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)  # Уникальное имя шаблона
    code = Column(String(64), nullable=False, unique=True)   # Код шаблона (welcome, password_reset, etc.)
    subject = Column(String(256), nullable=False)            # Тема письма
    html_content = Column(Text, nullable=False)              # HTML содержимое
    text_content = Column(Text, nullable=True)               # Текстовое содержимое (опционально)
    description = Column(Text, nullable=True)                # Описание назначения шаблона
    variables = Column(Text, nullable=True)                  # JSON с доступными переменными
    is_active = Column(Boolean, default=True)                # Активен ли шаблон
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(64), nullable=True)
    updated_by = Column(String(64), nullable=True) 