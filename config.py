# config.py
import os

class Config:
    _host_env = os.getenv('HOST')
    _locales_env = os.getenv('LOCALES')
    DEBUG = os.getenv('DEBUG', 'False')
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_NAMES = os.getenv('DATABASE_NAMES')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATION = os.getenv('SQLALCHEMY_TRACK_MODIFICATION')
    
    HOST = _host_env if _host_env else '0.0.0.0' if DEBUG == 'False' else 'localhost'
    LOCALES = _locales_env.split(',') if _locales_env else ['locale']
    
