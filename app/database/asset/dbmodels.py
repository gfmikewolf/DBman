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
        'readonly': {'id'}
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
        'readonly': {'id'}
    }

class Manager(Base):
    __tablename__ = 'manager'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    country_id: Mapped[int | None] = mapped_column(ForeignKey('country.id'))
    gender: Mapped[str | None]
    address: Mapped[str | None] = mapped_column(info={'longtext': True})
    email: Mapped[str | None]
    phone_number: Mapped[str | None]
    remarks: Mapped[str | None] = mapped_column(info={'longtext': True})
    extra_info: Mapped[DataJson | None] = mapped_column(DataJsonType)

    nationality: Mapped['Country'] = relationship(lazy='selectin')

    _name = synonym('name')

    key_info = {
        'data': (
            'id',
            'name',
            'country_id',
            'nationality',
            'gender',
            'address',
            'email',
            'phone_number',
            'remarks',
            'extra_info'
        ),
        'hidden': {'id', 'country_id'},
        'readonly': {'id', 'nationality'}
    }

class Country(Base):
    __tablename__ = 'country'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] 
    code: Mapped[str]

    _name = synonym('name')

    key_info = {
        'data': (
            'id',
            'name',
            'code'
        ),
        'hidden': {'id'},
        'readonly': {'id'}
    }

