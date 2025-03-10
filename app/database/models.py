# app/database/models.py
from .base import Base
from .contract import (
    Contract, 
    Amendment,
    Clause
)

DBModel: dict[str, type[Base]] = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause
}
