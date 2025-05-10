# app/database/contract/__init__.py

__all__ = [
    'ApplicableLaw',
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
        'ClauseCommercialIncentive',
        'ClauseSuspension',
        'ClauseCurrency',
        'ClauseProductLifecycle',
        'ClauseSLA',
        'ClauseNotice',
        'ClauseThirdPartyManagement',
        'ClauseCompliance',
        'ClauseApplicableLaw',
    'ClauseAction',
    'ClausePos',
    'ClauseType'
]

# database models
from .dbmodels import ApplicableLaw
from .dbmodels import Contract, ContractMAPContract, ContractLEGALMAPContract
from .dbmodels import Amendment
from .dbmodels import Scope, ScopeMAPScope
from .dbmodels import Entity
from .dbmodels import Entitygroup
from .dbmodels import Clause
from .dbmodels import ClauseCustomerList
from .dbmodels import ClauseScope
from .dbmodels import ClauseEntity
from .dbmodels import ClauseExpiry
from .dbmodels import ClauseTermination
from .dbmodels import ClauseWarrantyPeriod
from .dbmodels import ClauseCommercialIncentive
from .dbmodels import ClausePaymentTerm
from .dbmodels import ClauseSuspension
from .dbmodels import ClauseSLA
from .dbmodels import ClauseCurrency
from .dbmodels import ClauseProductLifecycle
from .dbmodels import ClauseNotice
from .dbmodels import ClauseThirdPartyManagement
from .dbmodels import ClauseApplicableLaw
from .dbmodels import ClauseCompliance

# type
from .types import ClauseAction, ClausePos, ClauseType

cache_map = {}

model_map = {
    'applicable_law': ApplicableLaw,
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
        'clause_sla': ClauseSLA,
        'clause_currency': ClauseCurrency,
        'clause_product_lifecycle': ClauseProductLifecycle,
        'clause_notice': ClauseNotice,
        'clause_tpm': ClauseThirdPartyManagement,
        'clause_compliance':ClauseCompliance,
        'clause_applicable_law': ClauseApplicableLaw
}

func_map = {}

table_map = {
    'basic': [
        'applicable_law',
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
    'commercial': [
        'clause_commercial_incentive',
        'clause_payment_term'
    ],
    'product': [
        'clause_product_lifecycle',
        'clause_tpm'
    ],
    'service clauses': [
        'clause_warranty_period',
        'clause_sla',
        'clause_suspension',
    ],
    'finance': [
        'clause_currency'
    ],
    'legal': [
        'clause_notice',
        'clause_compliance',
        'clause_applicable_law'
    ]
}
