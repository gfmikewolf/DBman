# app/database/contract/__init__.py

__all__ = [
    'Base'
]
from ..base import Base

# database models
from .dbmodels import Contract, ScopeMAPScope, UserMAPUserRole, UserRole
from .dbmodels import Amendment
from .dbmodels import Clause
from .dbmodels import Entity
from .dbmodels import Entitygroup
from .dbmodels import Scope
from .dbmodels import ClauseScope
from .dbmodels import ClauseEntity
from .dbmodels import ClauseExpiry
from .dbmodels import ContractMAPContract
from .dbmodels import ContractLEGALMAPContract
from .dbmodels import User
from .dbmodels import UserRole
from .dbmodels import UserMAPUserRole

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
    'clause_scope': ClauseScope,
    'contract__map__contract': ContractMAPContract,
    'contract__legal_map__contract': ContractLEGALMAPContract,
    'scope__map__scope': ScopeMAPScope,
    'user': User,
    'user_role': UserRole,
    'user__map__user_role': UserMAPUserRole
}

Base.func_map = {}
