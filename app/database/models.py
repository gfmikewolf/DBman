# app/database/models.py
__all__ = ['Base', 'Cache', 'table_map']
from .base import Base, Cache

table_map = {}
from .user import model_map as mm, table_map as tm, func_map as fm, cache_map as cm
Base.model_map.update(mm)
Base.func_map.update(fm)
Cache.cache_map.extend(cm)
table_map.update(tm)

from config import Config
if Config.TEST_APP == 'contract':
    from .contract import model_map as mm, table_map as tm, func_map as fm, cache_map as cm
else:
    from .asset import model_map as mm, table_map as tm, func_map as fm, cache_map as cm
    
Base.model_map.update(mm)
Base.func_map.update(fm)
Cache.cache_map.extend(cm)
table_map.update(tm)