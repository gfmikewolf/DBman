# app/database/__init__.py

# database models
from .dbmodels import Person
from .dbmodels import Area
from .dbmodels import Currency, HistoryExRate
from .dbmodels import Organization
from .dbmodels import Budget, BudgetMAPExpenseType
from .dbmodels import ExpenseType, ExpenseTypeMAPExpenseType
from .dbmodels import ExpenseMAPExpenseType 
from .dbmodels import (
    Asset, 
    AccountReceivable,
    CashEquivalent,
    Building,
    Vehicle,
    Crypto,
    TimeDeposit,
    Security, 
        Stock, PrivateStock, PublicStock, 
        Fund, PrivateFund, PublicFund
)
from .dbmodels import (
    Account, 
    BankAccount, 
    BrokerageAccount, 
    CryptoAccount, 
    CashAccount, 
    LoanAccount,
    DebitCard,
    CreditCard
)
from .dbmodels import (
    AccountTransaction,
    AssetTransaction,
    HistoryAccuAssetTransaction
)

cache_map = [
    HistoryExRate,
    Currency,
    HistoryAccuAssetTransaction
]

model_map = {
    'person': Person,
    'area': Area,
    'currency': Currency,
    'organization': Organization,
    'account': Account,
    'bank_account': BankAccount,
    'debit_card': DebitCard,
    'credit_card': CreditCard,
    'brokerage_account': BrokerageAccount,
    'crypto_account': CryptoAccount,
    'cash_account': CashAccount,
    'loan_account': LoanAccount,
    'other_account': Account,
    'budget__map__expense_type': BudgetMAPExpenseType,
    'expense_type': ExpenseType,
    'expense__map__expense_type': ExpenseMAPExpenseType,
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
    'asset_transaction': AssetTransaction,
    'cash_equivalent': CashEquivalent,
    'expense_type__map__expense_type': ExpenseTypeMAPExpenseType,
    'building': Building,
    'vehicle': Vehicle,
    'crypto': Crypto,
    'time_deposit': TimeDeposit,
    'history_accu_asset_transaction': HistoryAccuAssetTransaction,
    'history_ex_rate': HistoryExRate
}

func_map = {
    'account_transaction': {
        'load_statement': {
            'func_type': 'class',
            'input_types': {
                'account_id': ('_id.account', True),
                'statement': ('file-multiple', True)
            }
        }
    },
    'expense_type': {
        'update_expense_types': {
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
        'loan_account',
        'debit_card',
        'credit_card'
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
        'public_fund',
        'crypto',
        'time_deposit',
        'cash_equivalent',
        'building',
        'vehicle'
    ],
    'Transaction Class': [
        'account_transaction',
        'asset_transaction',
        'history_accu_asset_transaction'
    ],
    'Expense and Budget Class': [ 
        'budget__map__expense_type',
        'expense_type',
        'expense_type__map__expense_type',
        'expense__map__expense_type',
        'budget'
    ],
    'Financial Class': [
        'history_ex_rate'
    ]
}