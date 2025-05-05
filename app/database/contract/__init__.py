# app/database/contract/__init__.py

__all__ = [
    'Contract', 'ContractMAPContract', 'ContractLEGALMAPContract',
    'Amendment',
    'Scope', 'ScopeMAPScope',
    'Entity',
    'Entitygroup',
    'Clause',
        'ClauseCustomerList',
        'ClauseScope',
        'ClauseEntity',
        'ClauseExpiry',
        'ClauseTermination',
        'ClauseWarrantyPeriod',
        'ClausePaymentTerm',
    'ClauseAction',
    'ClausePos',
    'ClauseType',
    'ClauseCommercialIncentive'
]

# database models
from .dbmodels import Contract, ContractMAPContract, ContractLEGALMAPContract
from .dbmodels import Amendment
from .dbmodels import Scope, ScopeMAPScope
from .dbmodels import Entity
from .dbmodels import Entitygroup
from .dbmodels import (
    Clause,
    ClauseCustomerList,
    ClauseScope,
    ClauseEntity,
    ClauseExpiry,
    ClauseTermination,
    ClauseWarrantyPeriod,
    ClauseCommercialIncentive,
    ClausePaymentTerm,
    ClauseSuspension,
    ClauseSLA
)

# type
from .types import ClauseAction, ClausePos, ClauseType

cache_map = {}

model_map = {
    'contract': Contract,
        'contract__map__contract': ContractMAPContract,
        'contract__legal_map__contract': ContractLEGALMAPContract,
    'amendment': Amendment,
    'entity': Entity,
    'entitygroup': Entitygroup,
    'scope': Scope,
        'scope__map__scope': ScopeMAPScope,
    
    'clause': Clause,
        'clause_expiry': ClauseExpiry,
        'clause_entity': ClauseEntity,
        'clause_customer_list': ClauseCustomerList,
        'clause_scope': ClauseScope,
        'clause_termination': ClauseTermination,
        'clause_warranty_period': ClauseWarrantyPeriod,
        'clause_commercial_incentive': ClauseCommercialIncentive,
        'clause_payment_term': ClausePaymentTerm,
        'clause_suspension': ClauseSuspension,
        'clause_sla': ClauseSLA
}

func_map = {}

table_map = {
    'basic': [
        'contract',
        'amendment',
        'entity',
        'entitygroup',
        'scope',
        'scope__map__scope',
        'clause',
        'contract__map__contract',
        'contract__legal_map__contract'
    ],
    'entity clauses': [
        'clause_entity',
        'clause_customer_list'
    ],
    'scope clauses': [
        'clause_scope'
    ],
    'duration clauses': [
        'clause_expiry',
        'clause_termination'
    ],
    'service period clauses': [
        'clause_warranty_period'
    ],
    'commercial': [
        'clause_commercial_incentive',
        'clause_payment_term'
    ],
    'termination and suspension': [
        'clause_suspension'
    ],
    'other terms': [
        'clause_sla'
    ] 
}
