# app/database/__init__.py
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from .models import DBModel, Base

if Config.SQLALCHEMY_DATABASE_URI is None:
    raise ValueError("SQLALCHEMY_DATABASE_URI is not set in the configuration")

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True if Config.DEBUG=='True' else False)

db_session = scoped_session(
    sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
)
