# app/database/__init__.py
from ..base import Base

# database models
from .dbmodels import (
    ExpenseType, 
    AssetType, 
    Manager, 
    Area, 
    Currency,
    Organization,
    Account,
    BankAccount,
    BrokerageAccount,
    CryptoAccount,
    CashAccount,
    LoanAccount
)

# DataJson models

# type


Base.model_map = {
    'expense_type': ExpenseType, 
    'asset_type': AssetType,
    'manager': Manager,
    'area': Area,
    'currency': Currency,
    'organization': Organization,
    'account': Account,
    'bank_account': BankAccount,
    'brokerage_account': BrokerageAccount,
    'crypto_account': CryptoAccount,
    'cash_account': CashAccount,
    'loan_account': LoanAccount,
    'other_account': Account
}
