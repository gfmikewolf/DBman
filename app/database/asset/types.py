from enum import Enum

class AccountType(Enum):
    BANK_ACCOUNT = 'bank_account'
    BROKERAGE_ACCOUNT = 'brokerage_account'
    CASH_ACCOUNT = 'cash_account'
    CRYPTO_ACCOUNT = 'crypto_account'
    LOAN_ACCOUNT = 'loan_account'
    OTHER_ACCOUNT = 'other_account'

class Gender(Enum):
    M = 'Male'
    F = 'Female'

class AccountTransactionType(Enum):
    A = 'asset transaction'
    T = 'transfer'
    S = 'self transaction'

class AssetType(Enum):
    O = 'basic assets'
    AR = 'account receivables'
    S = 'securities'
    C = 'cash or cash equivalents'
    D = 'deposits'
    B = 'building'
    V = 'vehicles'
    
    S_S = 'stocks'
    S_S_PUB = 'publicly traded stocks'
    S_S_PRI = 'privately held stocks'

    S_F = 'funds'
    S_F_PRX = 'proxied funds'
    S_F_PUB = 'publicly traded funds'
    S_F_PRI = 'privately held funds'

    S_C = 'crypto'

    D_D = 'demand deposits'
    D_T = 'time deposits'