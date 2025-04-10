# app/database/__init__.py
from ..base import Base, DataJson

# database models
from .dbmodels import (
    ExpenseType, 
    AssetType, 
    Manager, 
    Area, 
    Currency,
    Organization,
    Account
)

# DataJson models

from .djmodels import (
    AccountExtraInfo,
    ManagerExtraInfo,
    OrganizationExtraInfo
)
# type


Base.model_map = {
    'expense_type': ExpenseType, 
    'asset_type': AssetType,
    'manager': Manager,
    'area': Area,
    'currency': Currency,
    'organization': Organization,
    'account': Account
}

DataJson.class_map = {
    'data_json': DataJson,
    'account_extra_info': AccountExtraInfo,
    'manager_extra_info': ManagerExtraInfo,
    'organization_extra_info': OrganizationExtraInfo
}
