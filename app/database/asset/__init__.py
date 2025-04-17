# app/database/__init__.py
from ..base import Base

# database models
from .dbmodels import (
    Person, 
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
    Budget,
    User,
    UserRole,
    UserMAPUserRole,
    Asset,
    AccountReceivable,
    Security,
    Stock,
    PrivateStock,
    PublicStock,
    Fund,
    PrivateFund,
    PublicFund,
    AccountTransaction,
    AccountTransfer,
)

Base.model_map = {
    'person': Person,
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
    'budget': Budget,
    'asset': Asset,
    'account_receivable': AccountReceivable,
    'security': Security,
    'stock': Stock,
    'private_stock': PrivateStock,
    'public_stock': PublicStock,
    'fund': Fund,
    'private_fund': PrivateFund,
    'public_fund': PublicFund,
    'account_transaction': AccountTransaction,
    'account_transfer': AccountTransfer,
    'user': User,
    'user_role': UserRole,
    'user__map__user_role': UserMAPUserRole
}

Base.func_map = {
    'expense': {
        'load_ADCB_account_statements': {
            'func_type': 'class',
            'input_types': {'ADCB_account_statements': ('file-multiple', True)}
        }
    },
    'budget': {
        'update_budgets': {
            'func_type': 'class',
            'input_types': {}
        }
    }
}

table_map = {
    'Basic Class': ['person', 'area', 'currency', 'organization'],
    'Account Class': [
        'account', 
        'bank_account', 
        'brokerage_account', 
        'crypto_account', 
        'cash_account', 
        'loan_account'
    ],
    'Asset Class': [
        'asset', 
        'account_receivable', 
        'security', 
        'stock', 
        'private_stock', 
        'public_stock', 
        'fund', 
        'private_fund', 
        'public_fund'
    ],
    'Transaction Class': [
        'account_transaction', 
        'account_transfer'
    ],
    'Expense and Budget Class': [
        'expense', 
        'budget__map__expense', 
        'budget'
    ],
    'User Management Class': [
        'user', 
        'user_role', 
        'user__map__user_role'
    ]
}