# database/asset/types.py
from enum import Enum
from datetime import date
from sqlalchemy import select
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dbmodels import Currency

class AccountType(Enum):
    BANK_ACCOUNT = 'bank account'
    BROKERAGE_ACCOUNT = 'brokerage account'
    CASH_ACCOUNT = 'cash account'
    CRYPTO_ACCOUNT = 'crypto account'
    LOAN_ACCOUNT = 'loan account'
    OTHER_ACCOUNT = 'other account'

    DEBIT_CARD = 'debit card'
    CREDIT_CARD = 'credit card'

class Gender(Enum):
    M = 'Male'
    F = 'Female'

class AccountTransactionType(Enum):
    ACCOUNT_TRANSFER = 'transfer'
    ACCOUNT_TRANSACTION = 'self transaction'
    ASSET_TRANSACTION = 'asset transaction'

class AssetType(Enum):
    ASSET = 'basic assets'
    ACCOUNT_RECEIVABLE = 'account receivables'
    SECURITY = 'securities'
    CASH_EQUIVALENT = 'cash or cash equivalents'
    DEPOSIT = 'deposits'
    BUILDING = 'building'
    VEHICLE = 'vehicles'
    
    STOCK = 'stocks'
    PUBLIC_STOCK = 'public stocks'
    PRIVATE_STOCK = 'private stocks'

    FUND = 'funds'
    PROXY_FUND = 'proxied funds'
    PUBLIC_FUND = 'public funds'
    PRIVATE_FUND = 'private funds'

    CRYPTO = 'crypto'

    DEMAND_DEPOSIT = 'demand deposits'
    TIME_DEPOSIT = 'time deposits'

class Amounts:
    @classmethod
    def ZERO(cls):
        obj = object.__new__(Amounts)
        obj.total = dict()
        obj.ex_rate = dict()
        obj.ex_date = None
        return obj
    def __init__(self, amount: float, currency: 'Currency', ex_date: date | None = None):
        self.total = dict()
        self.ex_rate = dict()
        self.ex_date = ex_date
        self.total[currency.code] = amount
        self.ex_rate[currency.code] = currency.get_ex_rate(ex_date)
    
    def __str__(self):
        return ', '.join([
            f'{amount:,.2f} {currency_code}'
            for currency_code, amount in self.total.items()
        ])
    
    def __repr__(self):
        return self.__str__()

    def __add__(self, other: 'Amounts') -> 'Amounts':
        result = object.__new__(self.__class__)
        result.total = sum_total = self.total.copy()
        result.ex_rate = self.ex_rate.copy()
        later = self
        new_keys = set()
        if (other.ex_date is None and self.ex_date is not None) or (self.ex_date and other.ex_date and other.ex_date > self.ex_date):
            result.ex_date = other.ex_date
            new_keys = self.ex_rate.keys() - other.ex_rate.keys()
            later = other
        elif (self.ex_date is None and other.ex_date is not None) or (self.ex_date and other.ex_date and self.ex_date > other.ex_date):
            result.ex_date = self.ex_date
            new_keys = other.ex_rate.keys() - self.ex_rate.keys()
        else:
            result.ex_date = self.ex_date
        if new_keys:
            from app.extensions import db_session
            with db_session() as sess:
                from app.database.asset.dbmodels import Currency
                new_currencies = sess.scalars(select(Currency).where(Currency.code.in_(new_keys))).all()
                for n_c in new_currencies:
                    result.ex_rate[n_c.code] = n_c.get_ex_rate(other.ex_date)
            result.ex_rate.update({c: r for c, r in later.ex_rate.items()})
        else:
            result.ex_rate.update(other.ex_rate)
        for currency_code, amount in other.total.items():
            if currency_code in sum_total:
                sum_total[currency_code] += amount
            else:
                sum_total[currency_code] = amount
        return result
    def __neg__(self) -> 'Amounts':
        result = object.__new__(self.__class__)
        result.total = dict()
        result.ex_date = self.ex_date
        result.ex_rate = self.ex_rate.copy()
        for c, a in self.total.items():
            result.total[c] = -a
        return result
    def __sub__(self, other: 'Amounts') -> 'Amounts':
        return self + (-other)

    def __mul__(self, other: float) -> 'Amounts':
        if not isinstance(other, (int, float)):
            raise TypeError(f'Cannot multiply Amounts by {type(other)}')
        mul_total = {currency_code: amount * other for currency_code, amount in self.total.items()}
        result = object.__new__(self.__class__)
        result.total = mul_total
        result.ex_date = self.ex_date
        result.ex_rate = self.ex_rate.copy()
        return result
    
    def __truediv__(self, other: float) -> 'Amounts':
        if not isinstance(other, (int, float)):
            raise TypeError(f'Cannot divide Amounts by {type(other)}')
        div_total = {currency_code: amount / other for currency_code, amount in self.total.items()}
        result = object.__new__(self.__class__)
        result.total = div_total
        result.ex_date = self.ex_date
        result.ex_rate = self.ex_rate.copy()
        return result
    
    def convert(self, target_currency: 'Currency', ex_date: date | None = None) -> float:
        total = 0.0
        for currency_code, amount in self.total.items():
            if currency_code == target_currency.code:
                total += amount
            elif currency_code in self.ex_rate:
                total += amount / self.ex_rate[currency_code] * target_currency.get_ex_rate(ex_date)
            else:
                raise ValueError(f'Currency {currency_code} not found in exchange rate')
        return total
    
    def to_dict(self) -> dict[str, float]:
        return {currency_code: amount for currency_code, amount in self.total.items()}
    
    def get_value(self, currency_code: str) -> float | None:
        return self.total.get(currency_code, None)
