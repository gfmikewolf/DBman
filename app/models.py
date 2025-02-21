# app/models.py
from app.base_mixin import Base, ForeignKeyMixin
from app.contract import (
    Contract, 
    Amendment,
    Clause,
    ClauseType,
    ClausePos,
    ClauseExpiry,
    ExpiryType
)

DBModel = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause,
    'clause_type': ClauseType,
    'clause_pos': ClausePos,
    'clause_expiry': ClauseExpiry,
    'expiry_type': ExpiryType
}
