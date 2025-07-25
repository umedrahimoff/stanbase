from db import Base
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, ForeignKey, Table
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
    deals = relationship('Deal', backref='company')
    jobs = relationship('Job', backref='company')
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
    currency_id = Column(Integer, ForeignKey('currency.id'))
    company_id = Column(Integer, ForeignKey('company.id'))
    investors = Column(String(256))
    status = Column(String(16), default='active')
    currency = relationship('Currency', backref='deals')

class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    country = Column(String(64))
    linkedin = Column(String(256))
    role = Column(String(64))
    status = Column(String(16), default='active')

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    slug = Column(String(256), unique=True, nullable=True)
    summary = Column(String(512))
    date = Column(Date, default=datetime.utcnow)
    content = Column(Text)
    views = Column(Integer, default=0)
    status = Column(String(16), default='active')
    author_id = Column(Integer, ForeignKey('author.id'), nullable=True)

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
    registration_url = Column(String(256))
    status = Column(String(16), default='active')

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(128), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
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

class Currency(Base):
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True)
    code = Column(String(8), unique=True, nullable=False)  # USD, EUR, KZT, etc.
    name = Column(String(64), nullable=False)  # Доллар США, Евро, Тенге
    symbol = Column(String(8))  # $, €, ₸
    status = Column(String(16), default='active') 