# app/database/__init__.py

# sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# app
from config import Config

__all__ = ['engine', 'db_session']

if Config.SQLALCHEMY_DATABASE_URI is None:
    raise ValueError("Invalid SQLALCHEMY_DATABASE_URI in env file")

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True if Config.DEBUG=='True' else False)

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)
