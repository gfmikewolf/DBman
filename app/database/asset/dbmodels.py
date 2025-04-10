from ast import For
from turtle import back
from sqlalchemy import Integer, String, Enum as SqlEnum, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, synonym, relationship
from app.database.types import DataJsonType
from ..base import Base, DataJson


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
    from .djmodels import ManagerExtraInfo
    extra_info: Mapped[ManagerExtraInfo | None] = mapped_column(DataJsonType)

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
            'remarks',
            'extra_info'
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
    from .djmodels import OrganizationExtraInfo
    extra_info: Mapped[DataJson | None] = mapped_column(DataJsonType)

    area: Mapped['Area'] = relationship(lazy='selectin')

    _name = synonym('nickname')

    key_info = {
        'data': (
            'id',
            'nickname',
            'fullname',
            'area_code',
            'area',
            'extra_info'
        ),
        'hidden': {'id', 'area_code'},
        'readonly': {'id', 'area'}
    }

class Account(Base):
    __tablename__ = 'account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str]
    identifier: Mapped[str | None]
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('manager.id'))
    financial_organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    currency_code: Mapped[str | None] = mapped_column(ForeignKey('currency.code'))
    from .djmodels import AccountExtraInfo
    extra_info: Mapped[AccountExtraInfo | None] = mapped_column(DataJsonType)

    owner: Mapped['Manager'] = relationship(lazy='selectin')
    financial_organization: Mapped['Organization'] = relationship(lazy='selectin')
    currency: Mapped['Currency'] = relationship(lazy='selectin')

    _name = synonym('nickname')

    key_info = {
        'data': (
            'id',
            'nickname',
            'identifier',
            'owner_id',
            'owner',
            'financial_organization_id',
            'financial_organization',
            'currency_code',
            'currency',
            'extra_info'
        ),
        'hidden': {'id', 'owner_id', 'financial_organization_id', 'currency_code'},
        'readonly': {'id', 'owner', 'financial_organization', 'currency'}
    }

