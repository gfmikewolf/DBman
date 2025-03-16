# app/database/models.py
from .datajson import DataJson
from .base import Base
from .contract import (
    Contract, 
    Amendment,
    Clause,
    Entity,
    Entitygroup,
    ClauseExpiry,
    ClauseEntity,
    ClauseScope
)

Base.model_map = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause,
    'entity': Entity,
    'entitygroup': Entitygroup
}

DataJson.class_map = {
    'base': DataJson,
    'expiry': ClauseExpiry,
    'entity': ClauseEntity,
    'scope': ClauseScope
}
