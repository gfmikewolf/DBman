# config.py
import os
from app.utils.common import get_translation_dict
from app.utils.translation_mj import TranslationMJ

class Config:
    _host_env = os.getenv('HOST')
    _locales_env = os.getenv('LOCALES')
    _langset_env = os.getenv('LANGSET')
    DEBUG = os.getenv('DEBUG', 'False')
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_NAMES = os.getenv('DATABASE_NAMES')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATION = os.getenv('SQLALCHEMY_TRACK_MODIFICATION')
    HOST = _host_env if _host_env else '0.0.0.0' if DEBUG == 'False' else 'localhost'
    SDICT_LIST = DATABASE_NAMES.split(',') if DATABASE_NAMES else []
    GDICT_LIST = _locales_env.split(',') if _locales_env else ['locale']
    LANGSET = _langset_env.split(',') if _langset_env else ['en', 'zh']
    TRANSLATOR = TranslationMJ(
        LANGSET,
        'en',
        get_translation_dict(LANGSET, GDICT_LIST),
        get_translation_dict(LANGSET, SDICT_LIST)
    )
    TEST_APP = os.getenv('TEST_APP')
