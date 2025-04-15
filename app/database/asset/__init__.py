# app/database/__init__.py
from ..base import Base

# database models
from .dbmodels import (
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
    LoanAccount,
    Expense,
    BudgetMAPExpense,
    Budget
)

Base.model_map = {
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
    'other_account': Account,
    'expense': Expense,
    'budget__map__expense': BudgetMAPExpense,
    'budget': Budget
}

Base.func_map = {
    'expense': {
        'load_ADCB_account_statement': {
            'func_type': 'class',
            'input_types': {'ADCB_account_statement':('file', True)}
        }
    },
    'budget': {
        'update_budgets': {
            'func_type': 'class',
            'input_types': {}
        }
    }
}