# app/database/contract/__init__.py

__all__ = [
    'Base'
]
from ..base import Base

# database models
from .dbmodels import (
    ClauseCustomerList,
    Contract,
    ScopeMAPScope,
    Amendment,
    Clause,
    Entity,
    Entitygroup,
    Scope,
    ClauseScope,
    ClauseEntity,
    ClauseCustomerList,
    ClauseExpiry,
    ClauseTermination,
    ContractMAPContract,
    ContractLEGALMAPContract
)

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
    'clause_customer_list': ClauseCustomerList,
    'clause_scope': ClauseScope,
    'clause_termination': ClauseTermination,
    'contract__map__contract': ContractMAPContract,
    'contract__legal_map__contract': ContractLEGALMAPContract,
    'scope__map__scope': ScopeMAPScope
}

Base.func_map = {}

table_map = {
    'basic': {
        'contract',
        'amendment',
        'entity',
        'entitygroup',
        'scope',
        'scope__map__scope',
        'clause',
        'contract__map__contract',
        'contract__legal_map__contract'
    },
    'entity clauses': {
        'clause_entity',
        'clause_customer_list'
    },
    'scope clauses': {
        'clause_scope'
    },
    'duration clauses': {
        'clause_expiry',
        'clause_termination'
    }
}
