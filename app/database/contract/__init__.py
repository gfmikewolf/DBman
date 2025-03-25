# app/database/__init__.py
from ..base import Base, DataJson

# database models
from .dbmodels import Contract
from .dbmodels import Amendment
from .dbmodels import Clause
from .dbmodels import Entity
from .dbmodels import Entitygroup

# DataJson models
from .clauses import ClauseEntity
from .clauses import ClauseExpiry
from .clauses import ClauseScope

# type Enums
from .clausetypes import ClauseAction, ClausePos, ClauseType

Base.model_map = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause,
    'entity': Entity,
    'entitygroup': Entitygroup
}

DataJson.class_map = {
    'data_json': DataJson,
    'clause_expiry': ClauseExpiry,
    'clause_entity': ClauseEntity,
    'clause_scope': ClauseScope
}
