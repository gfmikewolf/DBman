# app/database/models.py
from .contract import Base as DB_Contract, DataJson as DJ_Contract

DB_map = {
    'contract': DB_Contract
}

DJ_map = {
    'contract': DJ_Contract
}
