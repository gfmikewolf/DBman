from enum import Enum
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 仅供类型检查，运行时不导入，避免循环
    from .dbmodels import Currency

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

class Amounts:
    def __init__(self, amounts: set[tuple[float, 'Currency']], ex_date: date | None = None):
        from .dbmodels import Currency
        self.total = dict()
        self.ex_rate = dict()
        for amount, currency in amounts:
            if not isinstance(amount, (int, float)):
                raise TypeError(f'Amount must be int or float, got {type(amount)}')
            if not isinstance(currency, Currency):
                raise TypeError(f'Currency must be Currency object, got {type(currency)}')
            if ex_date and not isinstance(ex_date, date):
                raise TypeError(f'ex_date must be date object, got {type(ex_date)}')
            if ex_date and currency.code not in self.ex_rate:
                self.ex_rate[currency.code] = currency.get_ex_rate(ex_date)
            if currency.code in self.total:
                self.total[currency.code] += amount
            else:
                self.total[currency.code] = amount
    
    def __str__(self):
        return ','.join({f'{amount} {currency_code}' for amount, currency_code in self.total.items()})
    
    def __repr__(self):
        return self.__str__()

    def __add__(self, other: 'Amounts') -> 'Amounts':
        if not isinstance(other, Amounts):
            raise TypeError(f'Cannot add {type(other)} to Amounts')
        sum_total = self.total.copy()
        sum_ex_rate = self.ex_rate.copy()
        for currency_code, amount in other.total.items():
            if currency_code in sum_total:
                sum_total[currency_code] += amount
            else:
                sum_total[currency_code] = amount
        sum_ex_rate.update(other.ex_rate)
        result = object.__new__(self.__class__)
        result.total = sum_total
        result.ex_rate = sum_ex_rate
        return result

    def __sub__(self, other: 'Amounts') -> 'Amounts':
        if not isinstance(other, Amounts):
            raise TypeError(f'Cannot subtract {type(other)} from Amounts')
        diff_total = self.total.copy()
        diff_ex_rate = self.ex_rate.copy()
        for currency_code, amount in other.total.items():
            if currency_code in diff_total:
                diff_total[currency_code] -= amount
            else:
                diff_total[currency_code] = -amount
        diff_ex_rate.update(other.ex_rate)
        result = object.__new__(self.__class__)
        result.total = diff_total
        result.ex_rate = diff_ex_rate
        return result

    def __mul__(self, other: float) -> 'Amounts':
        if not isinstance(other, (int, float)):
            raise TypeError(f'Cannot multiply Amounts by {type(other)}')
        mul_total = {currency_code: amount * other for currency_code, amount in self.total.items()}
        result = object.__new__(self.__class__)
        result.total = mul_total
        result.ex_rate = self.ex_rate.copy()
        return result
    
    def __truediv__(self, other: float) -> 'Amounts':
        if not isinstance(other, (int, float)):
            raise TypeError(f'Cannot divide Amounts by {type(other)}')
        div_total = {currency_code: amount / other for currency_code, amount in self.total.items()}
        result = object.__new__(self.__class__)
        result.total = div_total
        result.ex_rate = self.ex_rate.copy()
        return result
    
    def convert(self, target_currency: 'Currency', ex_date: date | None = None) -> float:
        from .dbmodels import Currency
        if not isinstance(target_currency, Currency):
            raise TypeError(f'Target currency must be Currency object, got {type(target_currency)}')
        if ex_date and not isinstance(ex_date, date):
            raise TypeError(f'ex_date must be date object, got {type(ex_date)}')
        total = 0.0
        for currency_code, amount in self.total.items():
            if currency_code == target_currency.code:
                total += amount
            elif currency_code in self.ex_rate:
                total += amount / self.ex_rate[currency_code] * target_currency.get_ex_rate(ex_date)
            else:
                raise ValueError(f'Currency {currency_code} not found in exchange rate')
        return total