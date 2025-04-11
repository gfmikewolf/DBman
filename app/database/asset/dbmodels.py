from sqlalchemy import Integer, String, Enum as SqlEnum, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, synonym, relationship
from ..base import Base
from .types import AccountType


class ExpenseType(Base):
    __tablename__ = 'expense_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    frequency: Mapped[int]

    _name = synonym('name')

    key_info = {
        'data': (
            'id',
            'name'
        ),
        'hidden': { 'id' },
        'readonly': {'id'},
        'translate': { '_name'}
    }

class AssetType(Base):
    __tablename__ = 'asset_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    frequency: Mapped[int]

    _name = synonym('name')

    key_info = {
        'data': (
            'id',
            'name'
        ),
        'hidden': { 'id' },
        'readonly': {'id'},
        'translate': { '_name'}
    }

class Manager(Base):
    __tablename__ = 'manager'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    nationality_code: Mapped[str | None] = mapped_column(String, ForeignKey('area.code'))
    gender: Mapped[str | None]
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
        'translate': { '_name'}
    }

class Currency(Base):
    __tablename__ = 'currency'

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None]
    symbol: Mapped[str | None]

    _name = synonym('code')

    area: Mapped['Area'] = relationship(
        back_populates='currency',
        lazy='selectin')

    key_info = {
        'data': (
            'code',
            'name',
            'area',
            'symbol'
        ),
        'readonly': {'area'},
        'translate': { '_name' }
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
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('manager.id'))
    owner: Mapped['Manager'] = relationship(lazy='selectin')
    account_type: Mapped[AccountType] = mapped_column(SqlEnum(AccountType))
    currency_code: Mapped[str | None] = mapped_column(ForeignKey('currency.code'))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('account.id'))
    
    parent_account: Mapped['Account'] = relationship(lazy='selectin', remote_side=[id])
    
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
            'currency',
            'parent_id',
            'parent_account',
        ),
        'hidden': {'id', 'owner_id', 'currency_code', 'parent_id'},
        'readonly': {'id', 'owner', 'currency', 'parent_account'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.OTHER_ACCOUNT,
        'polymorphic_on': account_type
    }

class BankAccount(Account):
    __tablename__ = 'bank_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
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
            'currency',
            'IBAN',
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
            'currency_code',
            'currency',
            'account_number'
            'parent_id',
            'parent_account'
        ),
        'hidden': {'id', 'owner_id', 'currency_code', 'parent_id'},
        'readonly': {'id', 'owner', 'currency', 'parent_account'}
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
            'currency',
            'account_number',
            'organization_id',
            'organization'
            'parent_id',
            'parent_account'
        ),
        'hidden': {'id', 'owner_id', 'organization_id', 'currency_code', 'parent_id'},
        'readonly': {'id', 'owner', 'organization', 'currency', 'parent_account'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.LOAN_ACCOUNT,
    }
