# app/database/__init__.py
from ..base import Base

# database models
from .dbmodels import Contract
from .dbmodels import Amendment
from .dbmodels import Clause
from .dbmodels import Entity
from .dbmodels import Entitygroup
from .dbmodels import Scope
from .dbmodels import ClauseScope
from .dbmodels import ClauseEntity
from .dbmodels import ClauseExpiry


# type
from .types import ClauseAction, ClausePos, ClauseType

Base.model_map = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause,
    'entity': Entity,
    'scope': Scope,
    'entitygroup': Entitygroup,
    'clause_expiry': ClauseExpiry,
    'clause_entity': ClauseEntity,
    'clause_scope': ClauseScope
}
