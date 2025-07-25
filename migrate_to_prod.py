import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Company, Investor, News, Country, City, Category, CompanyStage, Author, Podcast, Event, Deal, Person, Job, PortfolioEntry

# Укажите строку подключения к прод-базе (например, из переменной окружения или напрямую)
PROD_DB_URL = os.getenv("DATABASE_URL")
LOCAL_DB_URL = "sqlite:///instance/stanbase.db"

local_engine = create_engine(LOCAL_DB_URL)
prod_engine = create_engine(PROD_DB_URL)

LocalSession = sessionmaker(bind=local_engine)
ProdSession = sessionmaker(bind=prod_engine)

def copy_table(local_session, prod_session, model):
    print(f"Copying {model.__tablename__} ...")
    items = local_session.query(model).all()
    for item in items:
        data = {c.name: getattr(item, c.name) for c in model.__table__.columns if c.name != 'id'}
        prod_session.add(model(**data))
    prod_session.commit()
    print(f"Done: {model.__tablename__}")

def main():
    local_session = LocalSession()
    prod_session = ProdSession()
    try:
        print(f"Подключение к прод-базе: {PROD_DB_URL}")
        # Порядок важен из-за внешних ключей
        for model in [Country, City, Category, CompanyStage, Author, Company, Investor, User, News, Podcast, Event, Deal, Person, Job, PortfolioEntry]:
            copy_table(local_session, prod_session, model)
    finally:
        local_session.close()
        prod_session.close()

if __name__ == "__main__":
    main() 