from enum import Enum

class AccountType(Enum):
    """Account type enum for SQLAlchemy."""
    BANK_ACCOUNT = 'bank_account'
    BROKERAGE_ACCOUNT = 'brokerage_account'
    CASH_ACCOUNT = 'cash_account'
    CRYPTO_ACCOUNT = 'crypto_account'
    LOAN_ACCOUNT = 'loan_account'
    OTHER_ACCOUNT = 'other_account'