# app/database.py
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from .models import DBModel, ForeignKeyMixin

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True if Config.DEBUG=='True' else False)

db_session = scoped_session(
    sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
)
