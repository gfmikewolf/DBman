# app/database/__init__.py
from ..base import Base, DataJson

# database models
from .dbmodels import ExpenseType, AssetType, Manager, Country

# DataJson models


# type


Base.model_map = {
    'expense_type': ExpenseType, 
    'asset_type': AssetType,
    'manager': Manager,
    'country': Country
}

DataJson.class_map = {
    'data_json': DataJson
}
