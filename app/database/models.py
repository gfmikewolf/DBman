# app/database/models.py
from .jsonbase import JsonBase
from .base import Base
from .contract import (
    Contract, 
    Amendment,
    Clause,
    ClauseExpiry,
    ClauseEntity,
    ClauseScope
)

Base.class_map = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause
}

JsonBase.class_map = {
    'base': JsonBase,
    'expiry': ClauseExpiry,
    'entity': ClauseEntity,
    'scope': ClauseScope
}
