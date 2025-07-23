from db import db
from datetime import datetime

startup_person = db.Table('startup_person',
    db.Column('startup_id', db.Integer, db.ForeignKey('startup.id')),
    db.Column('person_id', db.Integer, db.ForeignKey('person.id'))
)

investor_startup = db.Table('investor_startup',
    db.Column('investor_id', db.Integer, db.ForeignKey('investor.id')),
    db.Column('startup_id', db.Integer, db.ForeignKey('startup.id'))
)

investor_person = db.Table('investor_person',
    db.Column('investor_id', db.Integer, db.ForeignKey('investor.id')),
    db.Column('person_id', db.Integer, db.ForeignKey('person.id'))
)

class Startup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    country = db.Column(db.String(64))
    city = db.Column(db.String(64))
    stage = db.Column(db.String(32))
    industry = db.Column(db.String(64))
    founded_date = db.Column(db.Date)
    website = db.Column(db.String(256))
    team = db.relationship('Person', secondary=startup_person, backref='startups')
    deals = db.relationship('Deal', backref='startup')
    jobs = db.relationship('Job', backref='startup')
    status = db.Column(db.String(16), default='active')

class PortfolioEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    investor_id = db.Column(db.Integer, db.ForeignKey('investor.id'), nullable=False)
    startup_id = db.Column(db.Integer, db.ForeignKey('startup.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    valuation = db.Column(db.Float, nullable=True)
    # Для удобства связей
    investor = db.relationship('Investor', back_populates='portfolio_entries')
    startup = db.relationship('Startup')

class Investor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    country = db.Column(db.String(64))
    focus = db.Column(db.String(128))
    stages = db.Column(db.String(128))
    portfolio = db.relationship('Startup', secondary=investor_startup, backref='investors')
    portfolio_entries = db.relationship('PortfolioEntry', back_populates='investor', cascade='all, delete-orphan')
    team = db.relationship('Person', secondary=investor_person, backref='investor_teams')
    website = db.Column(db.String(256))
    status = db.Column(db.String(16), default='active')
    type = db.Column(db.String(16), default='angel')  # angel, venture, other

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32))
    amount = db.Column(db.Float)
    valuation = db.Column(db.Float, nullable=True)  # Новое поле: оценка
    date = db.Column(db.Date)
    currency = db.Column(db.String(8))
    startup_id = db.Column(db.Integer, db.ForeignKey('startup.id'))
    investors = db.Column(db.String(256))  # Список инвесторов (упрощённо для MVP)
    status = db.Column(db.String(16), default='active')

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    country = db.Column(db.String(64))
    linkedin = db.Column(db.String(256))
    role = db.Column(db.String(64))
    status = db.Column(db.String(16), default='active')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    summary = db.Column(db.String(512))
    date = db.Column(db.Date, default=datetime.utcnow)
    content = db.Column(db.Text)
    status = db.Column(db.String(16), default='active')
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=True)

class Podcast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    youtube_url = db.Column(db.String(256))
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(16), default='active')

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    startup_id = db.Column(db.Integer, db.ForeignKey('startup.id'))
    city = db.Column(db.String(64))
    job_type = db.Column(db.String(32))
    contact = db.Column(db.String(128))
    status = db.Column(db.String(16), default='active')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime)
    format = db.Column(db.String(32))
    location = db.Column(db.String(128))
    registration_url = db.Column(db.String(256)) 
    status = db.Column(db.String(16), default='active')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Хэш пароля
    role = db.Column(db.String(32), nullable=False)  # 'admin', 'moderator', 'investor', 'startuper'
    investor_id = db.Column(db.Integer, db.ForeignKey('investor.id'), nullable=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startup.id'), nullable=True) 
    status = db.Column(db.String(16), default='active')

class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(16), default='active')
    cities = db.relationship('City', backref='country', lazy=True)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    status = db.Column(db.String(16), default='active')

class StartupStage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    status = db.Column(db.String(16), default='active')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(16), default='active') 

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.String(256))
    status = db.Column(db.String(16), default='active')
    news = db.relationship('News', backref='author') 