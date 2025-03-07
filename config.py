# config.py
import os

class Config:
    _host_env = os.getenv('HOST')
    DEBUG = os.getenv('DEBUG', 'False') # 如果环境未设置调试参数，设为False
    HOST = _host_env if _host_env else '0.0.0.0' if DEBUG == 'False' else 'localhost'
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATION = os.getenv('SQLALCHEMY_TRACK_MODIFICATION')
    locales_env = os.getenv('LOCALES')
    LOCALES = locales_env.split(',') if locales_env else ['locale']
    
