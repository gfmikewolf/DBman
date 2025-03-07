# app/database/models.py
from .base import Base
from .contract import (
    Contract, 
    Amendment,
    Clause,
    ClauseType,
    ClausePos,
)

DBModel: dict[str, type[Base]] = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause,
    'clause_type': ClauseType,
    'clause_pos': ClausePos,
}
