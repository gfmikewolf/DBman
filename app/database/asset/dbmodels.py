import csv
import io
from typing import Any
from werkzeug.datastructures import FileStorage
from sqlalchemy import (
    Float, Integer, String, Enum as SqlEnum, Date, JSON,
    ForeignKey, 
    func,
    literal_column, insert, select
)
import bcrypt
from datetime import date, datetime
from sqlalchemy.orm import (
    mapped_column, Mapped, synonym, relationship, Session, aliased
)
from sqlalchemy.ext.hybrid import hybrid_property
from ..base import Base
from .types import AccountType, Gender, AssetType, AccountTransactionType

class Asset(Base):
    __tablename__ = 'asset'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    asset_type: Mapped[AssetType] = mapped_column(SqlEnum(AssetType))
    owner_id: Mapped[int] = mapped_column(ForeignKey('person.id'))
    owner: Mapped['Person'] = relationship(lazy='selectin')
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'), default='AED')
    currency: Mapped['Currency'] = relationship(lazy='selectin')
    remarks: Mapped[str | None] = mapped_column(info={'longtext': True})
    
    _name = synonym('name')
    
    __mapper_args__ = {
        'polymorphic_on': asset_type,
        'polymorphic_identity': AssetType.O
    }

    key_info = {
        'data': (
            'id',
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'currency_code'
        ),
        'hidden': { 'id', 'owner_id' },
        'readonly': {'id', 'owner' }
    }

class AccountReceivable(Asset):
    __tablename__ = 'account_receivable'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    amount: Mapped[float] = mapped_column(default=0.0)
    due_date: Mapped[date] = mapped_column(Date, default=date.today)
    
    _name = synonym('name')

    key_info = {
        'data': (
            'id',
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'amount',
            'currency_code',
            'due_date',
            'remarks'
        ),
        'hidden': { 'id', 'owner_id' },
        'readonly': {'id', 'owner' },
        'translate': { '_name'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AssetType.AR,
    }

class Security(Asset):
    __tablename__ = 'security'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey('organization.id'))
    issuer: Mapped['Organization'] = relationship(lazy='selectin')

    key_info = {
        'data': (
            'id',
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'issuer_id',
            'issuer',
            'currency_code'
        ),
        'hidden': { 'id', 'owner_id', 'issuer_id' },
        'readonly': {'id', 'owner', 'issuer' },
        'translate': { '_name', 'issuer' }
    }

    __mapper_args__ = {
        'polymorphic_identity': AssetType.S,
    }

class Stock(Security):
    __tablename__ = 'stock'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('security.id'), primary_key=True)
    unit_price: Mapped[float] = mapped_column(default=0.0)
    shares: Mapped[int] = mapped_column(default=0)
    company_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    company: Mapped['Organization'] = relationship(lazy='selectin')
    account_id: Mapped[int] = mapped_column(ForeignKey('brokerage_account.id'))

    @hybrid_property
    def market_value(self) -> float: # type: ignore
        return self.unit_price * self.shares
    
    @market_value.expression
    def market_value(cls):
        return func.cast(func.mul(cls.unit_price, cls.shares), Float)

    key_info = {
        'data': (
            'id',
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'issuer_id',
            'issuer',
            'market_value',
            'currency_code',
            'unit_price',
            'shares',
            'company_id',
            'company',
            'account_id',
            'account',
            'remarks'
        ),
        'hidden': { 'id', 'owner_id', 'issuer_id', 'company_id', 'account_id' },
        'readonly': {'id', 'owner', 'issuer', 'market_value', 'company', 'account' },
        'translate': { '_name', 'issuer', 'company' }
    }

    __mapper_args__ = {
        'polymorphic_identity': AssetType.S_S
    }

class PrivateStock(Stock):
    __tablename__ = 'private_stock'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('stock.id'), primary_key=True)
    days_to_liquidity: Mapped[int | None] = mapped_column(default=0)

    key_info = {
        'data': (
            'id',
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'issuer_id',
            'issuer',
            'market_value',
            'currency_code',
            'unit_price',
            'shares',
            'company_id',
            'company',
            'account_id',
            'account',
            'days_to_liquidity',
            'remarks'
        ),
        'hidden': { 'id', 'owner_id', 'issuer_id', 'company_id', 'account_id' },
        'readonly': {'id', 'owner', 'issuer', 'market_value', 'company', 'account' },
        'translate': { '_name', 'issuer', 'company' }
    }

    __mapper_args__ = {
        'polymorphic_identity': AssetType.S_S_PRI
    }

class PublicStock(Stock):
    __tablename__ = 'public_stock'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('stock.id'), primary_key=True)
    code: Mapped[str | None]

    __mapper_args__ = {
        'polymorphic_identity': AssetType.S_S_PUB
    }
    key_info = {
        'data': (
            'id',
            'name',
            'code',
            'asset_type',
            'owner_id',
            'owner',
            'issuer_id',
            'issuer',
            'market_value',
            'currency_code',
            'unit_price',
            'shares',
            'company_id',
            'company',
            'account_id',
            'account',
            'remarks'
        ),
        'hidden': { 'id', 'owner_id', 'issuer_id', 'company_id', 'account_id' },
        'readonly': {'id', 'owner', 'issuer', 'market_value', 'company', 'account' },
        'translate': { '_name', 'issuer', 'company' }
    }

class Fund(Security):
    __tablename__ = 'fund'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('security.id'), primary_key=True)
    
    key_info = {
        'data': (
            'id',
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'issuer_id',
            'issuer',
            'currency_code',
            'remarks'
        ),
        'hidden': { 'id', 'owner_id', 'issuer_id' },
        'readonly': {'id', 'owner', 'issuer' },
        'translate': { '_name', 'issuer' }
    }

    __mapper_args__ = {
        'polymorphic_identity': AssetType.S_F
    }

class PrivateFund(Fund):
    __tablename__ = 'private_fund'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('fund.id'), primary_key=True)
    days_to_liquidity: Mapped[int | None] = mapped_column(default=0)

    key_info = {
        'data': (
            'id',
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'issuer_id',
            'issuer',
            'market_value',
            'currency_code',
            'unit_price',
            'shares',
            'company_id',
            'company',
            'account_id',
            'account',
            'days_to_liquidity',
            'remarks'
        ),
        'hidden': { 'id', 'owner_id', 'issuer_id', 'company_id', 'account_id' },
        'readonly': {'id', 'owner', 'issuer', 'market_value', 'company', 'account' },
        'translate': { '_name', 'issuer', 'company' }
    }

    __mapper_args__ = {
        'polymorphic_identity': AssetType.S_F_PRI
    }

class PublicFund(Fund):
    __tablename__ = 'public_fund'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('fund.id'), primary_key=True)
    code: Mapped[str | None]

    __mapper_args__ = {
        'polymorphic_identity': AssetType.S_F_PUB
    }
    key_info = {
        'data': (
            'id',
            'name',
            'code',
            'asset_type',
            'owner_id',
            'owner',
            'issuer_id',
            'issuer',
            'market_value',
            'currency_code',
            'unit_price',
            'shares',
            'company_id',
            'company',
            'account_id',
            'account',
            'remarks'
        ),
        'hidden': { 'id', 'owner_id', 'issuer_id', 'company_id', 'account_id' },
        'readonly': {'id', 'owner', 'issuer', 'market_value', 'company', 'account' },
        'translate': { '_name', 'issuer', 'company' }
    }

class AccountTransaction(Base):
    __tablename__ = 'account_transaction'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    transaction_type: Mapped[AccountTransactionType] = mapped_column(SqlEnum(AccountTransactionType))
    account_id: Mapped[int] = mapped_column(ForeignKey('account.id'))
    amount: Mapped[float] = mapped_column(default=0.0)
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'), default='AED')
    remarks: Mapped[str | None] = mapped_column(info={'longtext': True})

    currency: Mapped['Currency'] = relationship(lazy='selectin')

    @property
    def _name(self):
        return f'{self.transaction_date}:{self.transaction_type}:{self.amount}{self.currency_code}'

    key_info = {
        'data': (
            'id',
            'transaction_date',
            'transaction_type',
            'account_id',
            'account',
            'amount',
            'currency_code'
            'remarks'
        ),
        'hidden': {'id', 'currency_code'},
        'readonly': {'id'},
        'translate': { '_name' }
    }

    __mapper_args__ = {
        'polymorphic_on': transaction_type,
        'polymorphic_identity': AccountTransactionType.S
    }

class AccountTransfer(AccountTransaction):
    __tablename__ = 'account_transfer'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account_transaction.id'), primary_key=True)
    from_account_id: Mapped[int] = mapped_column(ForeignKey('account.id'))
    to_account_id: Mapped[int] = mapped_column(ForeignKey('account.id'))

    from_account: Mapped['Account'] = relationship(lazy='selectin', foreign_keys=[from_account_id])
    to_account: Mapped['Account'] = relationship(lazy='selectin', foreign_keys=[to_account_id])

    key_info = {
        'data': (
            'id',
            'transaction_date',
            'transaction_type',
            'from_account_id',
            'from_account',
            'to_account_id',
            'to_account',
            'amount',
            'currency_code'
        ),
        'hidden': {'id', 'currency_code', 'from_account_id', 'to_account_id'},
        'readonly': {'id', 'from_account', 'to_account'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountTransactionType.T
    }

class Person(Base):
    __tablename__ = 'person'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    nationality_code: Mapped[str | None] = mapped_column(String, ForeignKey('area.code'))
    gender: Mapped[Gender | None] = mapped_column(SqlEnum(Gender))
    address: Mapped[str | None] = mapped_column(info={'longtext': True})
    email: Mapped[str | None]
    phone_number: Mapped[str | None]
    remarks: Mapped[str | None] = mapped_column(info={'longtext': True})

    nationality: Mapped['Area'] = relationship(lazy='selectin')
    accounts: Mapped[list['Account']] = relationship(
        back_populates='owner',
        lazy='select'
    )
    _name = synonym('name')

    key_info = {
        'data': (
            'id',
            'name',
            'nationality_code',
            'nationality',
            'gender',
            'address',
            'email',
            'phone_number',
            'remarks'
        ),
        'hidden': {'id', 'nationality_code'},
        'readonly': {'id', 'nationality'}
    }

class Area(Base):
    __tablename__ = 'area'

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'))
    
    _name = synonym('name')

    currency: Mapped['Currency'] = relationship(
        back_populates='area',
        lazy='selectin')
    
    key_info = {
        'data': (
            'code',
            'name',
            'currency_code',
            'currency'
        ),
        'hidden': {'id', 'currency_code'},
        'readonly': {'id', 'currency'},
        'translate': { '_name', 'name' }
    }

class Currency(Base):
    __tablename__ = 'currency'

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None]
    symbol: Mapped[str | None]
    exchange_rate_usd: Mapped[float] = mapped_column(default=1.0)

    _name = synonym('code')

    area: Mapped['Area'] = relationship(
        back_populates='currency',
        lazy='selectin')

    def get_ex_rate(self, date: date | None = None) -> float:
        if date:
            # search website for historical exchange rate
            pass
        return self.exchange_rate_usd
    
    key_info = {
        'data': (
            'code',
            'name',
            'area',
            'symbol'
        ),
        'readonly': {'area'},
        'translate': { '_name', 'name' }
    }

class Organization(Base):
    __tablename__ = 'organization'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str]
    fullname: Mapped[str | None]
    area_code: Mapped[str | None] = mapped_column(ForeignKey('area.code'))

    area: Mapped['Area'] = relationship(lazy='selectin')

    _name = synonym('nickname')

    key_info = {
        'data': (
            'id',
            'nickname',
            'fullname',
            'area_code',
            'area'
        ),
        'hidden': {'id', 'area_code'},
        'readonly': {'id', 'area'}
    }

class Account(Base):
    __tablename__ = 'account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str]
    owner_id: Mapped[int] = mapped_column(ForeignKey('person.id'))
    owner: Mapped['Person'] = relationship(lazy='selectin')
    account_type: Mapped[AccountType] = mapped_column(SqlEnum(AccountType))
    currency_code: Mapped[str | None] = mapped_column(ForeignKey('currency.code'))
    balance: Mapped[float] = mapped_column(default=0.0)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('account.id'))
    
    parent_account: Mapped['Account'] = relationship(
        back_populates='child_accounts',
        lazy='selectin', 
        remote_side=[id]
    )
    child_accounts: Mapped[list['Account']] = relationship(
        back_populates='parent_account',
        lazy='select'
    )

    currency: Mapped['Currency'] = relationship(lazy='selectin')

    _name = synonym('nickname')

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'currency_code',
            'balance',
            'cur_balance_total',
            'parent_id',
            'parent_account',
            'child_accounts'
        ),
        'hidden': {'id', 'owner_id', 'parent_id'},
        'readonly': {'id', 'owner', 'parent_account', 'child_accounts'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.OTHER_ACCOUNT,
        'polymorphic_on': account_type
    }
    
    from .types import Amounts
    def _fetch_total_amounts(self, ex_date: date | None = None) -> Amounts:
        from .types import Amounts
        if self.currency_code:
            amounts = Amounts({(self.balance, self.currency)})
        else:
            amounts = Amounts(set())
        for child_account in self.child_accounts:
            amounts += child_account._fetch_total_amounts()
        return amounts
    
    @property
    def cur_balance_total(self) -> str:
        return str(self._fetch_total_amounts())

class BankAccount(Account):
    __tablename__ = 'bank_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    account_name: Mapped[str | None]
    account_branch: Mapped[str | None]
    debit_cards: Mapped[str | None]
    credit_cards: Mapped[str | None]
    account_number: Mapped[str | None]
    IBAN: Mapped[str | None]

    organization: Mapped['Organization'] = relationship(lazy='selectin')

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'currency_code',
            'balance',
            'account_name',
            'account_branch',
            'debit_cards',
            'credit_cards',
            'IBAN',
            'account_number',
            'organization_id',
            'organization',
            'parent_id',
            'parent_account',
            'child_accounts'
        ),
        'hidden': {'id', 'owner_id', 'organization_id', 'parent_id'},
        'readonly': {'id', 'owner', 'organization', 'currency', 'parent_account', 'child_accounts'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.BANK_ACCOUNT,
    }

class CashAccount(Account):
    __tablename__ = 'cash_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    area_code: Mapped[str | None] = mapped_column(ForeignKey('area.code'))

    location: Mapped['Area'] = relationship(lazy='selectin')

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'currency_code',
            'currency',
            'area_code',
            'location',
            'parent_id',
            'parent_account'
        ),
        'hidden': {'id', 'owner_id', 'currency_code', 'area_code', 'parent_id'},
        'readonly': {'id', 'owner', 'currency', 'location', 'parent_account'}
    }

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'currency_code',
            'balance',
            'area_code',
            'location',
            'parent_id',
            'parent_account',
            'child_accounts'
        ),
        'hidden': {'id', 'owner_id', 'area_code', 'parent_id'},
        'readonly': {'id', 'owner', 'location', 'currency', 'parent_account', 'child_accounts'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.CASH_ACCOUNT,
    }

class BrokerageAccount(Account):
    __tablename__ = 'brokerage_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    account_number: Mapped[str | None]

    organization: Mapped['Organization'] = relationship(lazy='selectin')

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'currency_code',
            'currency',
            'account_number',
            'organization_id',
            'organization',
            'parent_id',
            'parent_account'
        ),
        'hidden': {'id', 'owner_id', 'organization_id', 'currency_code', 'parent_id'},
        'readonly': {'id', 'owner', 'organization', 'currency', 'parent_account'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.BROKERAGE_ACCOUNT,
    }

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'organization_id',
            'organization',
            'account_number',
            'currency_code',
            'balance',
            'parent_id',
            'parent_account',
            'child_accounts'
        ),
        'hidden': {'id', 'owner_id', 'parent_id', 'organization_id'},
        'readonly': {'id', 'owner', 'parent_account', 'child_accounts'}
    }
    
class CryptoAccount(Account):
    __tablename__ = 'crypto_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    account_number: Mapped[str | None]

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'account_number',
            'currency_code',
            'balance',
            'parent_id',
            'parent_account',
            'child_accounts'
        ),
        'hidden': {'id', 'owner_id', 'parent_id'},
        'readonly': {'id', 'owner', 'parent_account', 'child_accounts'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.CRYPTO_ACCOUNT,
    }

class LoanAccount(Account):
    __tablename__ = 'loan_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    account_number: Mapped[str | None]

    organization: Mapped['Organization'] = relationship(lazy='selectin')

    key_info = {
        'data': (
            'id',
            'nickname',
            'account_type',
            'owner_id',
            'owner',
            'currency_code',
            'balance',
            'account_number',
            'organization_id',
            'organization',
            'parent_id',
            'parent_account',
            'child_accounts'
        ),
        'hidden': {'id', 'owner_id', 'organization_id', 'parent_id'},
        'readonly': {'id', 'owner', 'organization', 'currency', 'parent_account', 'child_accounts'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.LOAN_ACCOUNT,
    }

class Expense(Base):
    __tablename__ = 'expense'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_date: Mapped[date] = mapped_column(Date, default=date.today)
    amount: Mapped[float] = mapped_column(default=0.0)
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'), default='AED')
    remarks: Mapped[str | None] = mapped_column(info={'longtext': True})

    currency: Mapped['Currency'] = relationship(lazy='selectin')
    budgets: Mapped[list['Budget']] = relationship(
        back_populates='expenses',
        secondary='budget__map__expense',
        lazy='select'
    )
    @hybrid_property
    def _name(self) -> str: # type: ignore
        return f'{self.expense_date} {self.amount} {self.currency_code}'
    
    @_name.expression
    def _name(cls):
        return (literal_column("expense.expense_date") + ' ' + literal_column("expense.amount") + ' ' + literal_column("expense.currency_code")).cast(String)
    
    key_info = {
        'data': (
            'id',
            'expense_date',
            'amount',
            'currency_code',
            'currency',
            'remarks',
            'budgets'
        ),
        'hidden': {'id', 'currency_code'},
        'readonly': {'id', 'currency', 'budgets'}
    }

    @classmethod
    def load_ADCB_account_statements(cls, db_session: Session, ADCB_account_statements: list[FileStorage]) -> dict[str, Any]:
        total_rows = 0
        for file in ADCB_account_statements:
            file.stream.seek(0)
            content = file.stream.read().decode("utf-8")
            lines = content.splitlines()
            if len(lines) < 10:
                return {'success': False, 'error': 'CSV content does not have enough lines (less than 10 lines)'}
            header_line = lines[7]
            data_lines = lines[9:]
            csv_data = "\n".join([header_line] + data_lines)
            stream = io.StringIO(csv_data)
            reader = csv.DictReader(stream, delimiter=',')
            rows_to_insert = []
            for row in reader:
                data = {}
                # 处理 Transaction Date 列——转换为 expense_date
                if 'Transaction Date' in row and row['Transaction Date']:
                    try:
                        dt = datetime.strptime(row['Transaction Date'].strip('"'), "%d/%m/%Y")
                        data['expense_date'] = dt.date()
                    except Exception:
                        return {'success': False, 'error': 'Invalid date format in row'}
                else:
                    continue
                if 'Amount in AED' in row and row['Amount in AED']:
                    try:
                        amount = float(row['Amount in AED'].replace(',', '').strip('"'))
                        if 'Cr/Dr' in row and row['Cr/Dr'].strip('"').upper() == "CR":
                            amount = -amount
                        data['amount'] = amount
                    except Exception:
                        return {'success': False, 'error': 'Invalid amount format in row'}
                if 'Description' in row:
                    data['remarks'] = row['Description'].strip('"')
                rows_to_insert.append(data)
            for data in rows_to_insert:
                expense = Expense(**data)
                db_session.add(expense)
            total_rows += len(rows_to_insert)
        try:
            db_session.commit()
            return {'success': True, 'data': f'{total_rows} records inserted'}
        except Exception as e:
            db_session.rollback()
            return {'success': False, 'error': str(e)}

class BudgetMAPExpense(Base):
    __tablename__ = 'budget__map__expense'
    budget_id: Mapped[int] = mapped_column(ForeignKey('budget.id'), primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey('expense.id'), primary_key=True)
    budget: Mapped['Budget'] = relationship(lazy='selectin', overlaps='expenses,budgets')
    expense: Mapped['Expense'] = relationship(lazy='selectin', overlaps='expenses,budgets')
    
    @hybrid_property
    def _name(self) -> str: # type: ignore
        return f'{self.budget.name} {self.expense._name}'
    
    @_name.expression
    def _name(cls):
        return (literal_column("budget.name") + ' ' + literal_column("expense._name")).cast(String)
    
    key_info = {
        'data': (
            'budget_id',
            'budget',
            'expense_id',
            'expense',
        ),
        'hidden': {'budget_id', 'expense_id'},
        'translate': {'_name'}
    }

class Budget(Base):
    __tablename__ = 'budget'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    keywords: Mapped[str | None] = mapped_column(info={'longtext': True})
    budget_total: Mapped[float] = mapped_column(default=0.0)
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'), default='AED')
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    _name = synonym('name')

    expenses: Mapped[list['Expense']] = relationship(
        back_populates='budgets',
        secondary='budget__map__expense',
        lazy='select',
    )
    currency: Mapped['Currency'] = relationship(lazy='selectin')

    @hybrid_property
    def expenses_total(self) -> float:  # type: ignore
        """
        先按每种支出币种累加 amount，再按汇率一次性换算为预算币种。
        """
        # 按币种累加
        sums: dict[str, float] = {}
        for exp in self.expenses:
            sums.setdefault(exp.currency_code, 0.0)
            sums[exp.currency_code] += exp.amount

        target_rate = self.currency.exchange_rate_usd
        total = 0.0
        # 按币种汇率换算
        rates_map = {e.currency_code: e.currency.exchange_rate_usd for e in self.expenses}
        for currency_code, amt in sums.items():
            if currency_code == self.currency_code:
                total += amt
            else:
                rate = rates_map[currency_code]
                total += amt * target_rate / rate
        return total

    @expenses_total.expression
    def expenses_total(cls):
        """
        SQL 先按币种分组求和，再按汇率转换并求总和。
        """
        exp_curr = aliased(Currency)
        bud_curr = aliased(Currency)
        # 子查询：按币种分组求和
        sub = (
            select(
                Expense.currency_code.label('cc'),
                func.sum(Expense.amount).label('sum_amt'),
            )
            .join(BudgetMAPExpense, BudgetMAPExpense.expense_id == Expense.id)
            .where(BudgetMAPExpense.budget_id == cls.id)
            .group_by(Expense.currency_code)
            .subquery()
        )
        # 主查询：连接币种表，按汇率换算并求总和
        expr = (
            select(
                func.coalesce(
                    func.sum(sub.c.sum_amt / exp_curr.exchange_rate_usd * bud_curr.exchange_rate_usd),
                    0.0
                )
            )
            .select_from(sub)
            .join(exp_curr, sub.c.cc == exp_curr.code)
            .join(bud_curr, bud_curr.code == cls.currency_code)
        )
        return expr.scalar_subquery()

    key_info = {
        'data': (
            'id',
            'name',
            'keywords',
            'budget_total',
            'expenses_total',
            'currency_code',
            'currency',
            'start_date',
            'end_date'
        ),
        'hidden': { 'id' },
        'readonly': {'id', 'expenses_total', 'currency'},
        'translate': { '_name', 'currency', 'name'}
    }

    @classmethod
    def update_budgets(cls, db_session: Session) -> dict[str, Any]:
        """
        Update BudgetMAPExpense table for each budget when an expense fits the
        keywords (comm-separated) of the budget and between the start_date and
        end_date of the budget.
        """
        budgets = db_session.query(Budget).filter(
            Budget.keywords != None,
            Budget.keywords != '',
        ).all()
        inserted_rows = 0
        for budget in budgets:
            expenses = db_session.query(Expense).filter(
                Expense.expense_date >= budget.start_date,
                Expense.expense_date <= budget.end_date
            ).all()
            new_mappings = []
            keywords = [k.strip() for k in budget.keywords.split(",") if k.strip()] # type: ignore
            for expense in expenses:
                if expense.remarks and any(keyword.lower() in expense.remarks.lower() for keyword in keywords):
                    new_mappings.append({'budget_id':budget.id, 'expense_id':expense.id})
            result = db_session.execute(insert(BudgetMAPExpense).prefix_with("OR IGNORE").values(new_mappings))
            inserted_rows += result.rowcount
        try:                
            db_session.commit()
            return {'success': True, 'data': f'{inserted_rows} records inserted'}
        except Exception as e:
            db_session.rollback()
            return {'success': False, 'error': str(e)}

class User(Base):
    __tablename__ = 'user'
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_password_hash: Mapped[str] = mapped_column(info={'password': True})
    user_name: Mapped[str]
    
    user_roles: Mapped[list['UserRole']] = relationship(
        back_populates='users',
        secondary=lambda: UserMAPUserRole.__table__,
        lazy='select'
    )
    
    @property
    def user_password(self):
        return None
    
    @user_password.setter
    def user_password(self, pw: str):
        self.user_password_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode(), self.user_password_hash.encode())

    key_info = {
        'data': (
            'user_id',
            'user_name',
            'user_password',
            'user_roles',
            'user_password_hash'
        ),
        'hidden': {
            'user_id',
            'user_password',
            'user_password_hash'
        },
        'readonly': {
            'user_id',
            'user_roles',
            'user_password_hash'
        },
        'password': { 'user_password' }
    }

class UserRole(Base):
    __tablename__ = 'user_role'
    user_role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_role_name: Mapped[str]
    table_privilege: Mapped[dict] = mapped_column(JSON)
    
    users: Mapped[list['User']] = relationship(
        back_populates='user_roles',
        secondary=lambda: UserMAPUserRole.__table__,
        lazy='select'
    )

    def __add__(self, other: 'UserRole') -> 'UserRole':
        if not isinstance(other, UserRole):
            return NotImplemented
        merged_priv = self.table_privilege or {}
        for k, v in (other.table_privilege or {}).items():
            if k in merged_priv:
                merged_priv[k] = ''.join(sorted(set(merged_priv[k]) | set(v)))
            else:
                merged_priv[k] = v
        merged = UserRole(user_role_name=f'{self.user_role_name}+{other.user_role_name}')
        merged.table_privilege = merged_priv
        return merged
    
    key_info = {
        'data': (
            'user_role_id',
            'user_role_name',
            'table_privilege',
            'users'
        ),
        'hidden': {
            'user_role_id'
        },
        'readonly': {
            'user_role_id',
            'users'
        }
    }

class UserMAPUserRole(Base):
    """
    .. example::
    ```python
    table_privilege = {'contract': 'ramd', ...}
    # r: read
    # a: append
    # m: modify
    # d: delete
    ```
    """
    __tablename__ = 'user__map__user_role'
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'), primary_key=True)
    user_role_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_role.user_role_id'), primary_key=True)
    key_info = {
        'data': (
            'user_id',
            'user_role_id',
            'user',
            'user_role'
        ),
        'hidden': {
            'user_id',
            'user_role_id'
        },
        'readonly': {
            'user',
            'user_role'
        }
    }