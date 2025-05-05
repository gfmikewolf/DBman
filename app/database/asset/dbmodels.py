# database/asset/__init__.py
__all__ = [
    'Asset',
    'AccountTransaction',
    'AccountTransfer',
    'AssetTransaction',
    'Person',
    'Area',
    'Currency',
    'Organization',
    'Account',
    'Building',
    'Vehicle',
    'Crypto',
    'TimeDeposit',
    'AccountReceivable',
    'Security',
    'Stock',
    'PrivateStock',
    'PublicStock',
    'Fund',
    'PrivateFund',
    'PublicFund',
    'CashEquivalent'
]

from abc import abstractmethod
from cProfile import label
from calendar import c
import csv
import itertools
from locale import currency
import logging
import re

from numpy import isin, record
from regex import P

from app.database import asset
logger = logging.getLogger(__name__)
from sqlite3 import DatabaseError
from typing import Any, Iterable
from datetime import date, datetime, timedelta
from werkzeug.datastructures import FileStorage

from sqlalchemy import DateTime, Integer, String, Enum as SqlEnum, Date, Transaction, literal, literal_column
from sqlalchemy import and_, case, or_, tuple_, cast
from sqlalchemy import ForeignKey
from sqlalchemy import event
from sqlalchemy import func
from sqlalchemy import insert, text, delete, select, update, union_all
from sqlalchemy.orm import reconstructor, mapped_column, relationship, aliased, object_session
from sqlalchemy.orm import Mapped, Session

from app.utils import xirr, get_stock_price

from ..base import Base, Cache
from .types import AccountType, Amounts, Gender, AssetType, AccountTransactionType


class Asset(Base):
    __tablename__ = 'asset'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    asset_type: Mapped[AssetType] = mapped_column(SqlEnum(AssetType))
    owner_id: Mapped[int] = mapped_column(ForeignKey('person.id'))
    owner: Mapped['Person'] = relationship(lazy='selectin')
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'), default='AED')
    currency: Mapped['Currency'] = relationship(lazy='selectin')
    remarks: Mapped[str | None]
    brokerage_account_id: Mapped[int | None] = mapped_column(ForeignKey('brokerage_account.id'))
    
    _xirr: dict[int, tuple[date, float]] = {}
    _cur_market_value: dict[int, tuple[date, float]] = {}
    
    brokerage_account: Mapped['BrokerageAccount'] = relationship(
        lazy='selectin',
        back_populates='assets'
    )
    asset_transactions: Mapped[list['AssetTransaction']] = relationship(
        back_populates='asset',
        lazy='select',
        order_by=lambda: AssetTransaction.transaction_date
    )
    latest_accu_transaction: Mapped['HistoryAccuAssetTransaction'] = relationship(
        primaryjoin=lambda: Asset.id == HistoryAccuAssetTransaction.asset_id,
        order_by=lambda: HistoryAccuAssetTransaction.record_date.desc(),
        uselist=False,
        viewonly=True,
        lazy='selectin'
    )
    accu_transactions: Mapped[list['HistoryAccuAssetTransaction']] = relationship(
        back_populates='asset',
        lazy='select'
    )
    @property
    def market_value(self) -> float:
        dv = Asset._cur_market_value.get(self.id, None)
        today = date.today()
        if (
            not dv
            or (
                isinstance(self, (PublicStock, PublicFund))
                and dv[0] != today
            )
        ):
            v = self.get_market_value()
            Asset._cur_market_value[self.id] = (today, v)
        return Asset._cur_market_value[self.id][1]

    @abstractmethod
    def get_market_value(self, dt: date = date.today()) -> float:
        raise NotImplementedError('get_market_value must be implemented in subclass of Asset')
    
    @property
    def total_investment(self) -> float:
        return self.latest_accu_transaction.investment
    
    @property
    def total_redemption(self) -> float:
        return self.latest_accu_transaction.redemption
    
    @property
    def original_market_value(self) -> float:
        return self.latest_accu_transaction.market_value
    
    @property
    def total_profit(self) -> float:
        return self.market_value - self.total_investment + self.total_redemption
    
    @property
    def total_profit_rate(self) -> str:
        return f'{(self.total_profit/self.total_investment) * 100.0:.2f}%'
    
    @property
    def extended_internal_rate_of_return(self) -> str:
        dx = Asset._xirr.get(self.id, None)
        today = date.today()
        if (
            not dx
            or (
                isinstance(self, (PublicStock, PublicFund))
                and dx[0] != today
            )
        ):
            cur_xirr = self.get_xirr()
            Asset._xirr[self.id] = (today, cur_xirr)
        return f'{Asset._xirr[self.id][1] * 100:,.2f}%'
    
    def get_xirr(self, dt: date = date.today()) -> float:
        flows = [
            (t.transaction_date, t.amount_change) 
            for t in self.asset_transactions 
            if t.transaction_date < dt
        ]
        if not flows:
            return 0.0
        flows.append((dt, self.market_value))
        try:
            cur_xirr = xirr(flows)
        except Exception as e:
            logger.error(f'Error calculating XIRR for asset {self.id}: {e}')
            cur_xirr = 0.0
        return cur_xirr            

    @property
    def total_quantity(self) -> float:
        return self.latest_accu_transaction.quantity
    
    @property
    def unit_cost(self) -> str:
        cost = self.total_investment - self.total_redemption
        if self.total_quantity == 0:
            value = cost
        else:
            value = cost / self.total_quantity
        return f'{value:,.2f}'

    def __str__(self) -> str:
        return f'{self.name} {self.currency_code} ∈ {self.owner.name}'
    
    __mapper_args__ = {
        'polymorphic_on': asset_type,
        'polymorphic_identity': AssetType.ASSET
    }
    data_list = [
            'name',
            'asset_type',
            'owner_id',
            'owner',
            'remarks',
            'brokerage_account_id',
            'brokerage_account',
            'currency_code',
            'market_value',
            'original_market_value',
            'total_profit_rate',
            'extended_internal_rate_of_return',
            'total_profit',
            'total_investment',
            'total_redemption',
            'total_quantity',
            'unit_cost' 
        ]
    key_info = {
        'hidden': { 
            'owner_id',
            'brokerage_account_id' 
        },
        'readonly': {
            'owner', 
            'market_value',
            'total_investment',
            'original_market_value',
            'total_profit',
            'total_profit_rate',
            'total_quantity',
            'unit_cost',
            'extended_internal_rate_of_return',
            'brokerage_account',
            'total_redemption'
        },
        'longtext': { 'remarks' }
    }

    @classmethod
    def update_cache(cls, db_session: Session) -> dict[str, Any]:
        if db_session is None:
            raise RuntimeError('Session is required to load Asset instance')
        cls._xirr.clear()
        cls._cur_market_value.clear()
        assets = db_session.scalars(select(cls)).all()
        if not assets:
            return {'success': True, 'data': 'No assets to update'}
        ids = [asset.id for asset in assets]
        HistoryAccuAssetTransaction.update_cache(db_session, ids)
        db_session.commit()
        today = date.today()
        for id, asset in zip(ids, assets):
            cls._cur_market_value[id] = (today, asset.market_value)
            if asset.latest_accu_transaction is None:
                Asset._xirr[asset.id] = (today, 0.0)
                continue
            db_session.expire(asset, ['latest_accu_transaction', 'accu_transactions'])
            today = date.today()
            if not isinstance(asset, (PublicStock, PublicFund)) or asset.latest_accu_transaction.record_date == today:
                Asset._xirr[asset.id] = (today, asset.latest_accu_transaction.xirr)
                continue
            flows = [
                (t.transaction_date, t.amount_change) 
                for t in asset.asset_transactions if t.transaction_date < today
            ]
            if not flows:
                Asset._xirr[asset.id] = (today, 0.0)
                continue
            flows.append((today, cls._cur_market_value[id][1]))
            try:
                Asset._xirr[asset.id] = (today, xirr(flows))
                continue
            except Exception as e:
                logger.error(f'Error calculating XIRR for asset {asset.id}: {e}')
                Asset._xirr[asset.id] = (today, 0.0)
        return {'success': True, 'message': f'{len(assets)} assets updated'}
class Building(Asset):
    __tablename__ = 'building'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    area_sqm: Mapped[float] = mapped_column(default=0.0)
    address: Mapped[str]
    area_code: Mapped[str] = mapped_column(ForeignKey('area.code'))
    location: Mapped['Area'] = relationship(lazy='selectin')
    price: Mapped[float] = mapped_column(default=0.0)

    def get_market_value(self, dt: date = date.today()) -> float:
        return self.price
    
    data_list = Asset.data_list + ['area_sqm', 'address', 'area_code', 'location', 'price']
    key_info = Asset.key_info.copy()
    key_info['hidden'] = Asset.key_info.get('hidden', set()) | {'area_code'}
    key_info['readonly'] = Asset.key_info.get('readonly', set()) | {'location'}
    
    __mapper_args__ = {
        'polymorphic_identity': AssetType.BUILDING,
    }
class Vehicle(Asset):
    __tablename__ = 'vehicle'
    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    brand: Mapped[str]
    model: Mapped[str]
    year: Mapped[int | None] = mapped_column(default=0)
    mileage: Mapped[float | None] = mapped_column(default=0.0)
    price: Mapped[float] = mapped_column(default=0.0)

    def get_market_value(self, dt: date = date.today()) -> float:
        return self.price
    
    data_list = Asset.data_list + ['brand', 'model', 'year', 'mileage', 'price']
    key_info = Asset.key_info.copy()
    
    __mapper_args__ = {
        'polymorphic_identity': AssetType.VEHICLE,
    }
class Crypto(Asset):
    __tablename__ = 'crypto'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    amount: Mapped[float] = mapped_column(default=0.0)

    def get_market_value(self, dt: date = date.today()) -> float:
        return self.amount
    
    key_info = Asset.key_info.copy()
    data_list = Asset.data_list + ['amount']

    __mapper_args__ = {
        'polymorphic_identity': AssetType.CRYPTO,
    }
class TimeDeposit(Asset):
    __tablename__ = 'time_deposit'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    amount: Mapped[float] = mapped_column(default=0.0)
    maturity_date: Mapped[date] = mapped_column(Date, default=date.today)
    early_termination_fee_pct: Mapped[float] = mapped_column(default=0.0)

    def get_market_value(self, dt: date = date.today()) -> float:
        sess = Session.object_session(self)
        if sess is None:
            raise RuntimeError('Session is required to load Asset instance')
        today = date.today()
        stmt = (
            select(AssetTransaction.transaction_date, AssetTransaction.amount_change).where(
                AssetTransaction.asset_id == self.id,
                AssetTransaction.transaction_date <= today
            ).order_by(AssetTransaction.transaction_date)
        )
        row = sess.execute(stmt).first()
        if row is None:
            return 0.0
        initial_date, initial_investment = row
        initial_investment = -initial_investment
        if dt < initial_date or dt > self.maturity_date:
            return 0.0
        period = (self.maturity_date - initial_date).days
        if period == 0:
            return 0.0
        return (
            initial_investment * (
                1 - self.early_termination_fee_pct / 100.0
            ) + (self.amount - initial_investment) * (
                (dt - initial_date).days / period
            )
        )

    key_info = Asset.key_info.copy()
    data_list = Asset.data_list + ['amount', 'maturity_date']
    key_info['hidden'] = Asset.key_info.get('hidden', set()) | {'amount'}

    __mapper_args__ = {
        'polymorphic_identity': AssetType.TIME_DEPOSIT,
    }
class AccountReceivable(Asset):
    __tablename__ = 'account_receivable'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    amount: Mapped[float] = mapped_column(default=0.0)
    due_date: Mapped[date] = mapped_column(Date, default=date.today)

    def get_market_value(self, dt: date = date.today()) -> float:
        return self.amount

    key_info = Asset.key_info.copy()
    data_list = Asset.data_list + ['amount', 'due_date']
    key_info['hidden'] = Asset.key_info.get('hidden', set()) | {'amount'}

    __mapper_args__ = {
        'polymorphic_identity': AssetType.ACCOUNT_RECEIVABLE,
    }
class CashEquivalent(Asset):
    __tablename__ = 'cash_equivalent'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    amount_or_quantity: Mapped[float] = mapped_column(default=0.0)
    cash_account_id: Mapped[int] = mapped_column(ForeignKey('cash_account.id'))
    cash_account: Mapped['CashAccount'] = relationship(lazy='selectin')
    
    def get_market_value(self, dt: date = date.today()) -> float:
        return self.amount_or_quantity
    
    key_info = Asset.key_info.copy()
    data_list = Asset.data_list + ['amount_or_quantity', 'cash_account_id', 'cash_account'] # type: ignore
    key_info['hidden'] = Asset.key_info.get('hidden', set()) | {'cash_account_id', 'amount_or_quantity'} # type: ignore
    key_info['readonly'] = Asset.key_info.get('readonly', set()) | {'cash_account'} # type: ignore

    __mapper_args__ = {
        'polymorphic_identity': AssetType.CASH_EQUIVALENT
    }
class Security(Asset):
    __tablename__ = 'security'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('asset.id'), primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey('organization.id'))
    issuer: Mapped['Organization'] = relationship(lazy='selectin')

    def get_market_value(self, dt: date = date.today()) -> float:
        raise NotImplementedError('market_value must be implemented in subclass of Security')
    
    key_info = Asset.key_info.copy()
    data_list = Asset.data_list + ['issuer_id', 'issuer']
    key_info['hidden'] = key_info.get('hidden', set()) | {'issuer_id', 'brokerage_account_id'}
    key_info['readonly'] = key_info.get('readonly', set()) | {'issuer'}
    key_info['translate'] = key_info.get('translate', set()) | {'issuer'}

    __mapper_args__ = {
        'polymorphic_identity': AssetType.SECURITY,
    }
class Stock(Security):
    __tablename__ = 'stock'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('security.id'), primary_key=True)
    unit_price: Mapped[float] = mapped_column(default=0.0)
    shares: Mapped[float] = mapped_column(default=0.0)
    company_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    company: Mapped['Organization'] = relationship(lazy='selectin')
    
    @property
    def latest_unit_price(self) -> float:
        web_price_func = getattr(self, 'web_price', None) 
        if web_price_func:
            return web_price_func()
        else:
            return self.unit_price

    def get_market_value(self, dt: date = date.today()) -> float:
        return self.latest_unit_price * self.shares
    
    key_info = Security.key_info.copy()
    data_list = Security.data_list + [
        'unit_price', 
        'shares', 
        'company_id', 
        'company',
        'latest_unit_price'
    ]
    key_info['hidden'] = key_info.get('hidden', set()) | {
        'company_id',
        'unit_price'
    }
    key_info['readonly'] = key_info.get('readonly', set()) | {
        'company',
        'latest_unit_price'
    }
    key_info['translate'] = key_info.get('translate', set()) | {'company'}
    
    __mapper_args__ = {
        'polymorphic_identity': AssetType.STOCK
    }
class PrivateStock(Stock):
    __tablename__ = 'private_stock'

    id: Mapped[int] = mapped_column(ForeignKey('stock.id'), primary_key=True)
    days_to_liquidity: Mapped[int | None] = mapped_column(default=0)

    key_info = Stock.key_info.copy()
    data_list = Stock.data_list + ['days_to_liquidity']

    __mapper_args__ = {
        'polymorphic_identity': AssetType.PRIVATE_STOCK
    }
class PublicStock(Stock):
    __tablename__ = 'public_stock'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('stock.id'), primary_key=True)
    code: Mapped[str | None]
    
    def web_price(self, dt: date | None = None) -> float | None:
        if not self.code:
            return None
        return get_stock_price(self.code, dt) if dt else get_stock_price(self.code)

    key_info = Stock.key_info.copy()
    data_list = Stock.data_list + ['code']

    __mapper_args__ = {
        'polymorphic_identity': AssetType.PUBLIC_STOCK
    }
class Fund(Security):
    __tablename__ = 'fund'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('security.id'), primary_key=True)
    
    def get_market_value(self, dt: date = date.today()) -> float:
        raise NotImplementedError('market_value must be implemented in subclass of Fund')
    
    key_info = Security.key_info.copy()
    data_list = Security.data_list.copy()
    
    __mapper_args__ = {
        'polymorphic_identity': AssetType.FUND
    }
class PrivateFund(Fund):
    __tablename__ = 'private_fund'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('fund.id'), primary_key=True)
    cur_value: Mapped[float] = mapped_column(default=0.0)
    days_to_liquidity: Mapped[int | None] = mapped_column(default=0)

    def get_market_value(self, dt: date = date.today()) -> float:
        return self.cur_value
    
    key_info = Fund.key_info.copy()
    data_list = Fund.data_list + ['cur_value', 'days_to_liquidity']

    __mapper_args__ = {
        'polymorphic_identity': AssetType.PRIVATE_FUND
    }
class PublicFund(Fund):
    __tablename__ = 'public_fund'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('fund.id'), primary_key=True)
    code: Mapped[str | None]
    unit_price: Mapped[float] = mapped_column(default=0.0)
    units: Mapped[float] = mapped_column(default=0.0)

    def get_market_value(self, dt: date = date.today()) -> float:
        return self.unit_price * self.units
    
    key_info = Fund.key_info.copy()
    data_list = Fund.data_list + ['code', 'unit_price', 'units']

    __mapper_args__ = {
        'polymorphic_identity': AssetType.PUBLIC_FUND
    }

class AccountTransaction(Base):
    __tablename__ = 'account_transaction'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    transaction_type: Mapped[AccountTransactionType] = mapped_column(SqlEnum(AccountTransactionType))
    account_id: Mapped[int] = mapped_column(ForeignKey('account.id'))
    account: Mapped['Account'] = relationship(lazy='selectin')
    amount_change: Mapped[float] = mapped_column(default=0.0)
    remarks: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expense_types: Mapped[list['ExpenseType']] = relationship(
        back_populates='expenses',
        secondary='expense__map__expense_type',
        lazy='selectin',
        order_by=lambda: ExpenseType.name
    )
    @property
    def amount(self) -> Amounts:
        return Amounts(abs(self.amount_change), self.account.currency)
    
    @property
    def category(self) -> str:
        if self.amount_change < 0:
            return 'expense'
        elif self.amount_change > 0:
            return 'income'
        else:
            return 'no change'

    def __str__(self):
        return f'{self.category}:{self.amount}@{self.transaction_date} {self.transaction_type.name}'

    __mapper_args__ = {
        'polymorphic_on': transaction_type,
        'polymorphic_identity': AccountTransactionType.ACCOUNT_TRANSACTION
    }

    data_list = [
        'id',
        'transaction_date',
        'category',
        'amount',
        'amount_change',
        'remarks',
        'transaction_type',
        'account_id',
        'account'
    ]
    key_info = {
        'hidden': {'id', 'account_id', 'amount_change'},
        'readonly': {'id', 'account', 'category', 'amount'},
        'longtext': {'remarks'},
        'translate': { '_self', 'category' }
    }
    
    @classmethod
    def load_statement(cls, db_session: Session, account_id: int, statement: list[FileStorage]) -> dict[str, Any]:
        total_rows = 0
        for file in statement:
            file.stream.seek(0)
            content = file.stream.read().decode("utf-8")
            lines = content.splitlines(keepends=True)
            line1 = lines[0].lstrip('\ufeff').strip().strip('"')
            line4 = lines[3].lstrip('\ufeff').strip().strip('"')
            if line4.startswith('Credit'): # credit card found
                if len(lines) < 9:
                    return {'success': False, 'error': 'CSV content does not have enough lines (less than 10 lines)'}
                header_line = lines[7]
                data_lines = lines[9:]
                reader = csv.DictReader(itertools.chain([header_line], data_lines), delimiter=',')
                rows_to_insert = []
                for row in reader:
                    data = {}
                    if 'Transaction Date' in row and row['Transaction Date']:
                        try:
                            dt = datetime.strptime(row['Transaction Date'].strip('"'), "%d/%m/%Y")
                            data['transaction_date'] = dt.date()
                        except Exception:
                            return {'success': False, 'error': 'Invalid date format in row'}
                    else:
                        continue
                    if 'Amount in AED' in row and row['Amount in AED']:
                        try:
                            amount = float(row['Amount in AED'].replace(',', '').strip('"'))
                            if 'Cr/Dr' in row and row['Cr/Dr'].strip('"').upper() == "DR":
                                amount = -amount
                            data['amount_change'] = amount
                        except Exception:
                            return {'success': False, 'error': 'Invalid amount format in row'}
                    if 'Description' in row:
                        data['remarks'] = row['Description'].strip('"')
                    data['account_id'] = account_id
                    data['transaction_type'] = AccountTransactionType.ACCOUNT_TRANSACTION
                    rows_to_insert.append(data)
                for data in rows_to_insert:
                    transaction = AccountTransaction(**data)
                    db_session.add(transaction)
                total_rows += len(rows_to_insert)
            elif line4.startswith('Account'): # account
                if len(lines) < 8:
                    return {'success': False, 'error': 'CSV content does not have enough lines (less than 10 lines)'}
                reader = csv.DictReader(lines[6:], delimiter=',')
                rows_to_insert = []
                for row in reader:
                    data = {}
                    if 'Value Date' in row and row['Value Date']:
                        try:
                            dt = datetime.strptime(row['Value Date'].strip('"'), "%d/%m/%Y")
                            data['transaction_date'] = dt.date()
                        except Exception:
                            return {'success': False, 'error': 'Invalid date format in row'}
                    else:
                        continue
                    if 'Credit Amount' in row and row['Credit Amount'] and 'Debit Amount' in row and row['Debit Amount']:
                        try:
                            data['amount_change'] = float(row['Credit Amount'].replace(',', '').strip('"')) - float(row['Debit Amount'].replace(',', '').strip('"'))
                        except Exception:
                            return {'success': False, 'error': 'Invalid amount format in row'}
                    if 'Description' in row:
                        data['remarks'] = row['Description'].strip('"')
                    data['account_id'] = account_id
                    data['transaction_type'] = AccountTransactionType.ACCOUNT_TRANSACTION
                    rows_to_insert.append(data)
                for data in rows_to_insert:
                    transaction = AccountTransaction(**data)
                    db_session.add(transaction)
                total_rows += len(rows_to_insert)
            elif line1.startswith('微信'):
                if len(lines) < 18:
                    return {'success': False, 'error': 'CSV content does not have enough lines (less than 20 lines)'}
                reader = csv.DictReader(lines[16:], delimiter=',')
                rows_to_insert = []
                for row in reader:
                    data = {}
                    try:
                        dt = datetime.strptime(row['交易时间'].strip('"').strip(), "%Y/%m/%d %H:%M")
                        data['transaction_date'] = dt.date()
                    except Exception:
                        return {'success': False, 'error': 'Invalid date format in row'}
                    if row['收/支'] in ['收入', '支出']:
                        try:
                            amount_change = float(row['金额(元)'][1:].replace(',', ''))
                            if row['收/支'] == '支出':
                                amount_change = -amount_change
                            data['amount_change'] = amount_change
                        except Exception:
                            return {'success': False, 'error': 'Invalid amount format in row'}
                    else: 
                        continue
                    data['remarks'] = f'{row['交易类型']} {row['交易对方']} {row['商品']}'
                    data['account_id'] = account_id
                    data['transaction_type'] = AccountTransactionType.ACCOUNT_TRANSACTION
                    rows_to_insert.append(data)
                for data in rows_to_insert:
                    transaction = AccountTransaction(**data)
                    db_session.add(transaction)
                total_rows += len(rows_to_insert)
        if total_rows == 0:
            return {'success': False, 'error': 'No valid data found in the files'}
        try:
            db_session.commit()
            return {'success': True, 'data': f'{total_rows} records inserted'}
        except Exception as e:
            db_session.rollback()
            return {'success': False, 'error': str(e)}
class AssetTransaction(AccountTransaction):
    __tablename__ = 'asset_transaction'
    id: Mapped[int] = mapped_column(Integer, ForeignKey('account_transaction.id'), primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey('asset.id'))
    asset: Mapped['Asset'] = relationship(
        back_populates='asset_transactions',
        lazy='selectin'
    )
    market_value_change: Mapped[float] = mapped_column(default=0.0)
    quantity_change: Mapped[float] = mapped_column(default=0.0)

    @property
    def category(self) -> str:
        if self.amount_change < 0:
            if self.market_value_change > 0:
                return 'investment'
            else:
                return 'loss'
        elif self.amount_change > 0:
            if self.market_value_change < 0:
                return 'redemption'
            elif self.market_value_change == 0:
                return 'cash_dividend'
            else:
                return 'asset_dividend & cash_dividend'
        else:
            if self.quantity_change > 0:
                return 'asset_dividend'
            elif self.quantity_change < 0:
                if self.market_value_change > 0:
                    return 'asset_quantity_loss & value appreciation'
                elif self.market_value_change < 0:
                    return 'asset_quantity_loss & value depreciation'
                else:
                    return 'asset_quantity_loss'
            else:
                if self.market_value_change < 0:
                    return 'value depreciation'
                elif self.market_value_change == 0:
                    return 'no change'
                else:
                    return 'value appreciation'

    __mapper_args__ = {
        'polymorphic_identity': AccountTransactionType.ASSET_TRANSACTION
    }

    key_info = AccountTransaction.key_info.copy()
    data_list = AccountTransaction.data_list + [
        'asset_id', 'asset', 'market_value_change', 'quantity_change'
    ]
    key_info['hidden'] = AccountTransaction.key_info.get('hidden', set()) | {'asset_id'}
    key_info['readonly'] = AccountTransaction.key_info.get('readonly', set()) | {'asset'}
    
class Person(Base):
    __tablename__ = 'person'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    nationality_code: Mapped[str | None] = mapped_column(String, ForeignKey('area.code'))
    gender: Mapped[Gender | None] = mapped_column(SqlEnum(Gender))
    address: Mapped[str | None]
    email: Mapped[str | None]
    phone_number: Mapped[str | None]
    remarks: Mapped[str | None]
    nationality: Mapped['Area'] = relationship(lazy='selectin')
    currency_code: Mapped[str | None] = mapped_column(ForeignKey('currency.code'))
    currency: Mapped['Currency | None'] = relationship(lazy='selectin')
    accounts: Mapped[list['Account']] = relationship(
        back_populates='_owner',
        lazy='selectin'
    )
    assets: Mapped[list['Asset']] = relationship(
        back_populates='owner',
        lazy='selectin'
    )
    
    @property
    def total_balance(self) -> Amounts:
        total = Amounts.ZERO()
        for account in self.accounts:
            if account.parent_id is None:
                total += account.total_balance
        return total

    @property
    def market_value(self) -> Amounts:
        total = Amounts.ZERO()
        for asset in self.assets:
            if not isinstance(asset, CashEquivalent):
                total += Amounts(asset.market_value, asset.currency)
        return total
    
    @property
    def total_value(self) -> float:
        return (self.total_balance + self.market_value).convert(self.currency) if self.currency else 0.0

    def __str__(self) -> str:
        return self.name

    data_list = [
        'name',
        'nationality_code',
        'nationality',
        'gender',
        'address',
        'email',
        'phone_number',
        'remarks',
        'currency_code',
        'total_balance',
        'market_value',
        'total_value'
    ]
    key_info = {
        'hidden': {'nationality_code', 'currency_code'},
        'readonly': {'nationality', 'total_balance', 'market_value', 'total_value'},
        'longtext': {'remarks', 'address'}
    }

class Area(Base):
    __tablename__ = 'area'

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    parent_code: Mapped[str | None] = mapped_column(ForeignKey('area.code'))

    parent_area: Mapped['Area'] = relationship(
        back_populates='child_areas',
        remote_side=[code],
        lazy='selectin'
    )
    child_areas: Mapped[list['Area']] = relationship(
        back_populates='parent_area',
        remote_side=[parent_code],
        lazy='selectin'
    )

    def __str__(self):
        return self.name
    
    data_list = [
        'code',
        'name',
        'parent_code',
        'parent_area'
    ]
    key_info = {
        'hidden': {'code', 'parent_code'},
        'readonly': {'parent_area'},
        'viewable_list': {'child_areas'},
        'translate': { '_self', 'name' }
    }

class Currency(Base):
    __tablename__ = 'currency'

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None]
    symbol: Mapped[str | None]
    ex_rate: Mapped[float] = mapped_column(default=1.0)

    history_rates: Mapped[list['HistoryExRate']] = relationship(
        back_populates='currency',
        lazy='select'
    )

    def __str__(self) -> str:
        return self.code
    data_list = [
        'code',
        'name',
        'symbol',
        'ex_rate'
    ]
    key_info = {
        'translate': {'name'}
    }

    def get_ex_rate(self, dt: date | None = None) -> float:
        if date:
            for rate in self.history_rates:
                if rate.ex_date == dt:
                    return rate.ex_rate
        return self.ex_rate
    
    @classmethod
    def update_ex_rate(cls, db_session: Session) -> bool:
        """
        Update the exchange rate as of today for all currencies.
        """
        try:
            currencies = db_session.scalars(select(cls)).all()
            for currency in currencies:
                rate = get_stock_price(f'{currency.code}USD=X')
                if rate:
                    currency.ex_rate = rate
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error updating exchange rates: {e}")
            return False

class Organization(Base):
    __tablename__ = 'organization'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str]
    fullname: Mapped[str | None]
    area_code: Mapped[str | None] = mapped_column(ForeignKey('area.code'))

    area: Mapped['Area'] = relationship(lazy='selectin')

    def __str__(self) -> str:
        return self.nickname

    data_list = [
        'nickname',
        'fullname',
        'area_code',
        'area'
    ]
    key_info = {
        'hidden': {'area_code'},
        'readonly': {'area'}
    }

class Account(Base):
    __tablename__ = 'account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str]
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('person.id'))
    _owner: Mapped['Person'] = relationship(lazy='selectin')
    @property
    def owner(self) -> 'Person | None':
        if self.owner_id is not None:
            return self._owner
        if self.parent_account:
            return self.parent_account.owner
        return None
    account_type: Mapped[AccountType] = mapped_column(SqlEnum(AccountType))
    currency_code: Mapped[str | None] = mapped_column(ForeignKey('currency.code'))
    balance: Mapped[float] = mapped_column(default=0.0)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('account.id'))
    remarks: Mapped[str | None]
    parent_account: Mapped['Account'] = relationship(
        back_populates='child_accounts',
        lazy='selectin', 
        remote_side=[id]
    )
    child_accounts: Mapped[list['Account']] = relationship(
        back_populates='parent_account',
        lazy='selectin'
    )
    currency: Mapped['Currency'] = relationship(lazy='selectin')
    transactions: Mapped[list['AccountTransaction']] = relationship(
        back_populates='account',
        lazy='select',
        order_by=lambda: AccountTransaction.transaction_date
    )

    @property
    def total_balance(self) -> 'Amounts':
        total = Amounts(self.balance, self.currency) if self.currency else Amounts.ZERO()
        for a in self.child_accounts:
            total += a.total_balance
        return total
    @property
    def normalized_balance(self) -> 'Amounts':
        return Amounts(self.total_balance.convert(self.currency), self.currency) if self.currency else Amounts.ZERO()
    
    def __str__(self) -> str:
        return f'{self.nickname} ∈ {self.owner}'
    
    data_list = [
        'nickname',
        'account_type',
        'owner_id',
        'owner',
        'currency_code',
        'balance',
        'normalized_balance',
        'total_balance',
        'parent_id',
        'parent_account',
        'child_accounts',
        'remarks'
    ]
    key_info = {
        'hidden': {
            'owner_id', 
            'parent_id', 
            'currency_code', 
            'balance'
        },
        'readonly': {
            'owner', 
            'parent_account', 
            'child_accounts', 
            'total_balance',
            'normalized_balance',
        },
        'longtext': {'remarks'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.OTHER_ACCOUNT,
        'polymorphic_on': account_type
    }
    
    from .types import Amounts
    def _fetch_total_amounts(self) -> Amounts:
        from .types import Amounts
        if self.currency_code:
            sess = Session.object_session(self)
            if sess is None:
                raise ValueError('Session is not available')
            sess.scalar(select())
            amounts = Amounts(self.balance, self.currency)
        else: # no currency assigned, assume multi-currency account
            amounts = Amounts.ZERO()
        for child_account in self.child_accounts:
            amounts += child_account._fetch_total_amounts()
        return amounts  
class BankAccount(Account):
    __tablename__ = 'bank_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    account_name: Mapped[str | None]
    account_branch: Mapped[str | None]
    account_number: Mapped[str | None]
    IBAN: Mapped[str | None]

    organization: Mapped['Organization'] = relationship(lazy='selectin')

    key_info = Account.key_info.copy()
    data_list = Account.data_list + [
        'organization_id', 'organization', 
        'account_name', 'account_branch',  
        'account_number', 
        'IBAN']
    key_info['hidden'] = Account.key_info.get('hidden', set()) | {'organization_id'}
    key_info['readonly'] = Account.key_info.get('readonly', set()) | {'organization'}

    __mapper_args__ = {
        'polymorphic_identity': AccountType.BANK_ACCOUNT,
    }
class DebitCard(Account):
    __tablename__ = 'debit_card'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    card_number: Mapped[str | None]
    card_name: Mapped[str]
    expiry_date: Mapped[date | None] = mapped_column(Date)
    account_branch: Mapped[str | None]
    
    key_info = Account.key_info.copy()
    data_list = Account.data_list + [
        'card_name', 
        'card_number', 
        'expiry_date', 
        'account_branch'
    ]

    __mapper_args__ = {
        'polymorphic_identity': AccountType.DEBIT_CARD,
    }
class CreditCard(Account):
    __tablename__ = 'credit_card'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    card_name: Mapped[str]
    card_number: Mapped[str | None]
    expiry_date: Mapped[date | None] = mapped_column(Date)
    credit_limit: Mapped[float | None] = mapped_column(default=0.0)

    key_info = Account.key_info.copy()
    data_list = Account.data_list + ['card_name', 'card_number', 'expiry_date', 'credit_limit']

    __mapper_args__ = {
        'polymorphic_identity': AccountType.CREDIT_CARD,
    }
class CashAccount(Account):
    __tablename__ = 'cash_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    area_code: Mapped[str | None] = mapped_column(ForeignKey('area.code'))

    location: Mapped['Area'] = relationship(lazy='selectin')

    cash_equivalents: Mapped[list['CashEquivalent']] = relationship(
        back_populates='cash_account',
        lazy='selectin'
    )

    @property
    def total_balance(self) -> Amounts:
        total = Amounts.ZERO()
        for ce in self.cash_equivalents:
            total += Amounts(ce.market_value, ce.currency)
        if self.currency_code:
            return Amounts(total.convert(self.currency), self.currency)
        return total

    key_info = Account.key_info.copy()
    data_list = Account.data_list + ['area_code', 'location']
    key_info['hidden'] = Account.key_info.get('hidden', set()) | {'area_code'}
    key_info['readonly'] = Account.key_info.get('readonly', set()) | {'location'}

    __mapper_args__ = {
        'polymorphic_identity': AccountType.CASH_ACCOUNT,
    }
class BrokerageAccount(Account):
    __tablename__ = 'brokerage_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    account_number: Mapped[str | None]

    organization: Mapped['Organization'] = relationship(lazy='selectin')
    assets: Mapped[list['Asset']] = relationship(
        back_populates='brokerage_account',
        lazy='select'
    )
    external_transactions: Mapped[list['BrokerageAccountExternalTransaction']] = relationship(
        back_populates='brokerage_account',
        lazy='select'
    )
    
    @property
    def market_value(self) -> float:
        return self._market_value

    @property
    def total_investment(self) -> float:
        return self._total_investment
    
    @property
    def total_redemption(self) -> float:
        return self._total_redemption
    
    @property
    def total_profit(self) -> float:
        return self._total_profit
    
    @property
    def total_profit_rate(self) -> str:
        return f'{self._total_profit_rate*100:.2f}%'
    
    @property
    def extended_internal_rate_of_return(self) -> str:
        return f'{self._xirr:,.2f}%'
    
    

    key_info = Account.key_info.copy()
    data_list = Account.data_list + [
        'organization_id', 
        'organization', 
        'account_number',
        'total_profit_rate',
        'extended_internal_rate_of_return',
        'total_investment',
        'total_profit',
        'total_redemption'
        'market_value'
    ]
    key_info['hidden'] = Account.key_info.get('hidden', set()) | {
        'organization_id'
    }
    key_info['readonly'] = Account.key_info.get('readonly', set()) | {
        'organization',
        'total_profit',
        'total_investment',
        'total_redemption',
        'total_profit_rate',
        'extended_internal_rate_of_return'
        'market_value'
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.BROKERAGE_ACCOUNT,
    }

    # cache for related accounts and assets
    _related_accounts: list['Account'] = []
    _related_assets: list['Asset'] = []

    @property
    def related_accounts(self) -> list['Account']:
        if not self._related_accounts:
            self._related_accounts = self.get_related_accounts()
        return self._related_accounts

    def get_related_accounts(self) -> list['Account']:
        acct_cte = select(BrokerageAccount.id).where(BrokerageAccount.id == self.id).cte(recursive=True)
        child = aliased(BrokerageAccount)
        acct_cte = acct_cte.union_all(
            select(child.id).where(child.parent_id == acct_cte.c.id)
        )
        stmt = select(Account).where(Account.id.in_(select(acct_cte.c.id)))
        sess = object_session(self)
        if sess is None:
            raise ValueError('Session is not available')
        return list(sess.scalars(stmt).all())

    @property
    def related_assets(self) -> list['Asset']:
        if not self._related_assets:
            self._related_assets = self.get_related_assets()
        return self._related_assets

    def get_related_assets(self) -> list['Asset']:
        acct_cte = select(BrokerageAccount.id).where(BrokerageAccount.id == self.id).cte(recursive=True)
        child = aliased(BrokerageAccount)
        acct_cte = acct_cte.union_all(
            select(child.id).where(child.parent_id == acct_cte.c.id)
        )
        stmt = select(Asset).where(Asset.brokerage_account_id.in_(select(acct_cte.c.id)))
        sess = object_session(self)
        if sess is None:
            raise ValueError('Session is not available')
        return list(sess.scalars(stmt).all())
    
class CryptoAccount(Account):
    __tablename__ = 'crypto_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    account_number: Mapped[str | None]

    key_info = Account.key_info.copy()
    data_list = Account.data_list + ['account_number']

    __mapper_args__ = {
        'polymorphic_identity': AccountType.CRYPTO_ACCOUNT,
    }
class LoanAccount(Account):
    __tablename__ = 'loan_account'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organization.id'))
    account_number: Mapped[str | None]

    organization: Mapped['Organization'] = relationship(lazy='selectin')

    key_info = Account.key_info.copy()
    data_list = Account.data_list + ['organization_id', 'organization', 'account_number']
    key_info['hidden'] = Account.key_info.get('hidden', set()) | {'organization_id'}

    __mapper_args__ = {
        'polymorphic_identity': AccountType.LOAN_ACCOUNT,
    }

class BudgetMAPExpense(Base):
    __tablename__ = 'budget__map__expense'
    budget_id: Mapped[int] = mapped_column(ForeignKey('budget.id'), primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey('account_transaction.id'), primary_key=True)
    budget: Mapped['Budget'] = relationship(lazy='selectin', overlaps='expenses,budgets')
    expense: Mapped['AccountTransaction'] = relationship(lazy='selectin', overlaps='expenses,budgets')
    
    def __str__(self) -> str:
        return f'{self.budget.name} {self.expense}'

    data_list = [
        'budget_id',
        'budget',
        'expense_id',
        'expense'
    ]
    key_info = {
        'hidden': {'budget_id', 'expense_id'},
        'translate': {'_self'}
    }

class ExpenseType(Base):
    __tablename__ = 'expense_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    keywords: Mapped[str | None]
    remarks: Mapped[str | None]
    recent_frequency: Mapped[int] = mapped_column(default=0)
    expenses: Mapped[list['AccountTransaction']] = relationship(
        back_populates='expense_types',
        lazy='selectin',
        secondary=lambda: ExpenseMAPExpenseType.__table__,
        primaryjoin=lambda: ExpenseMAPExpenseType.expense_type_id == ExpenseType.id,
        secondaryjoin=lambda: ExpenseMAPExpenseType.expense_id == AccountTransaction.id,
    )
    budgets: Mapped[list['Budget']] = relationship(
        back_populates='expense_types',
        lazy='selectin',
        secondary=lambda: BudgetMAPExpenseType.__table__,
        primaryjoin=lambda: BudgetMAPExpenseType.expense_type_id == ExpenseType.id,
        secondaryjoin=lambda: BudgetMAPExpenseType.budget_id == Budget.id,
    )
    parent_expense_types: Mapped[list['ExpenseType']] = relationship(
        back_populates='child_expense_types',
        lazy='selectin',
        secondary=lambda: ExpenseTypeMAPExpenseType.__table__,
        primaryjoin=lambda: ExpenseTypeMAPExpenseType.child_id == ExpenseType.id,
        secondaryjoin=lambda: ExpenseTypeMAPExpenseType.parent_id == ExpenseType.id,
    )
    child_expense_types: Mapped[list['ExpenseType']] = relationship(
        back_populates='parent_expense_types',
        lazy='selectin',
        secondary=lambda: ExpenseTypeMAPExpenseType.__table__,
        primaryjoin=lambda: ExpenseTypeMAPExpenseType.parent_id == ExpenseType.id,
        secondaryjoin=lambda: ExpenseTypeMAPExpenseType.child_id == ExpenseType.id,
    )

    def __str__(self) -> str:
        return self.name
    data_list = [
        'name',
        'keywords',
        'remarks',
        'parent_expense_types',
        'child_expense_types',
    ]
    key_info = {
        'readonly': {'parent_expense_types', 'child_expense_types'},
        'longtext': {'remarks', 'keywords'},
        'translate': {'name', '_self'}
    }
    @classmethod
    def update_expense_types(cls, db_session: Session) -> dict[str, Any]:
        """
        Update ExpenseMAPExpenseType table for each expense_type when an expense fits the
        keywords (comma-separated) of the expense_type.
        """
        db_session.execute(delete(ExpenseMAPExpenseType))
        db_session.flush()
        expense_types = db_session.query(ExpenseType).filter(
            ExpenseType.keywords != None,
            ExpenseType.keywords != '',
        ).all()
        inserted_rows = 0

        expenses = db_session.query(AccountTransaction).filter(
            AccountTransaction.amount_change < 0.0,
            AccountTransaction.remarks != None,
            AccountTransaction.transaction_type == AccountTransactionType.ACCOUNT_TRANSACTION
        ).all()

        for expense_type in expense_types:
            new_mappings = []
            keywords = [k.strip() for k in expense_type.keywords.split(",") if k.strip()]  # type: ignore
            for expense in expenses:
                text = (expense.remarks or '').strip().lower()
                if any(kw.lower() in text for kw in keywords):
                    new_mappings.append({
                        'expense_type_id': expense_type.id,
                        'expense_id': expense.id
                    })

            if new_mappings:
                result = db_session.execute(
                    insert(ExpenseMAPExpenseType)
                        .prefix_with("OR IGNORE")
                        .values(new_mappings)
                )
                inserted_rows += result.rowcount
        
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            return {'success': False, 'error': str(e)}
        # 统计过去 12 个月内每个 expense_type 出现次数，写入 recent_frequency
        cutoff = date.today() - timedelta(days=365)
        subq = (
            select(
                ExpenseMAPExpenseType.expense_type_id.label('et_id'),
                func.count().label('cnt')
            )
            .join(AccountTransaction)
            .where(
                AccountTransaction.transaction_date >= cutoff,
                AccountTransaction.amount_change < 0.0,
            )
            .group_by(ExpenseMAPExpenseType.expense_type_id)
            .subquery()
        )
        stmt = (
            update(ExpenseType)
            .values(recent_frequency=subq.c.cnt)
            .where(ExpenseType.id == subq.c.et_id)
        )
        db_session.execute(stmt)
        try:
            db_session.commit()
            return {
                'success': True,
                'data': f'{inserted_rows} mappings inserted; updated recent_frequency'
            }
        except Exception as e:
            db_session.rollback()
            return {'success': False, 'error': str(e)}
   
class ExpenseTypeMAPExpenseType(Base):
    __tablename__ = 'expense_type__map__expense_type'
    parent_id: Mapped[int] = mapped_column(ForeignKey('expense_type.id'), primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey('expense_type.id'), primary_key=True)
    parent: Mapped['ExpenseType'] = relationship(
        lazy='selectin', 
        foreign_keys=[parent_id],
        overlaps='child_expense_types,parent_expense_types'
    )
    child: Mapped['ExpenseType'] = relationship(
        lazy='selectin', 
        foreign_keys=[child_id],
        overlaps='parent_expense_types,child_expense_types'
    )
    def __str__(self) -> str:
        return f'{self.child.name} ∈ {self.parent.name}'
    
    data_list = [
        'parent_id',
        'parent',
        'child_id',
        'child'
    ]
    key_info = {
        'hidden': {'parent_id', 'child_id'},
        'readonly': {'parent', 'child'},
        'translate': {'_self'}
    }

class ExpenseMAPExpenseType(Base):
    __tablename__ = 'expense__map__expense_type'
    expense_id: Mapped[int] = mapped_column(ForeignKey('account_transaction.id'), primary_key=True)
    expense_type_id: Mapped[int] = mapped_column(ForeignKey('expense_type.id'), primary_key=True)
    expense: Mapped['AccountTransaction'] = relationship(lazy='selectin', overlaps='expenses,expense_types')
    expense_type: Mapped['ExpenseType'] = relationship(lazy='selectin', overlaps='expenses,expense_types')

    def __str__(self) -> str:
        return f'{self.expense} {self.expense_type}'
    
    data_list = [
        'expense_id',
        'expense',
        'expense_type_id',
        'expense_type'
    ]
    key_info = {
        'hidden': {'expense_id', 'expense_type_id'},
        'translate': {'_self'}
    }

class Budget(Base):
    __tablename__ = 'budget'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    budget_total: Mapped[float] = mapped_column(default=0.0)
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'), default='AED')
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    expense_types: Mapped[list['ExpenseType']] = relationship(
        back_populates='budgets',
        secondary='budget__map__expense_type',
        lazy='selectin'
    )
    currency: Mapped['Currency'] = relationship(lazy='selectin')

    @property
    def expenses_total(self) -> 'Amounts':
        sql = text("""
        WITH RECURSIVE et(id) AS (
            SELECT expense_type_id
              FROM budget__map__expense_type
             WHERE budget_id = :budget_id
            UNION
            SELECT m.child_id
              FROM expense_type__map__expense_type AS m
              JOIN et ON m.parent_id = et.id
        )
        SELECT
            SUM(
                ABS(sub.amount_change)
                / src.ex_rate
                * tgt.ex_rate
            ) AS total_converted
        FROM (
            SELECT DISTINCT at.id, at.amount_change, a.currency_code
              FROM account_transaction AS at
              JOIN expense__map__expense_type AS em 
                ON em.expense_id = at.id
              JOIN account AS a 
                ON at.account_id = a.id
             WHERE em.expense_type_id IN (SELECT id FROM et)
               AND at.transaction_date BETWEEN :start AND :end
               AND at.amount_change < 0
        ) AS sub
        JOIN currency AS src 
          ON sub.currency_code = src.code
        JOIN budget AS b 
          ON b.id = :budget_id
        JOIN currency AS tgt 
          ON b.currency_code = tgt.code;
        """)
        db_session = Session.object_session(self)
        if db_session is None:
            raise ValueError("No active session found")
        result = db_session.execute(sql, {
            'budget_id': self.id,
            'start': self.start_date,
            'end': self.end_date
        }).scalar() or 0.0
        return Amounts(result, self.currency)


    @property
    def completion_rate(self) -> float:
        if self.budget_total == 0:
            return 0.0
        return self.expenses_total.convert(self.currency) / self.budget_total

    @property
    def completion_pct(self) -> str:
        return f'{self.completion_rate * 100.0:.2f}%'
    
    def __str__(self) -> str:
        return f'{self.name}'
    
    data_list = [
        'name',
        'budget_total',
        'expenses_total',
        'completion_pct',
        'currency_code',
        'start_date',
        'end_date'
    ]
    key_info = {
        'hidden': {'currency_code' },
        'readonly': {'expenses_total', 'completion_pct'},
        'translate': { '_self', 'name'}
    }

class BudgetMAPExpenseType(Base):
    __tablename__ = 'budget__map__expense_type'
    budget_id: Mapped[int] = mapped_column(ForeignKey('budget.id'), primary_key=True)
    expense_type_id: Mapped[int] = mapped_column(ForeignKey('expense_type.id'), primary_key=True)
    budget: Mapped['Budget'] = relationship(lazy='selectin', overlaps='expense_types,budgets')
    expense_type: Mapped['ExpenseType'] = relationship(lazy='selectin', overlaps='expense_types,budgets')

    def __str__(self) -> str:
        return f'{self.expense_type.name} ∈ {self.budget.name}'
    
    data_list = [
        'budget_id',
        'budget',
        'expense_type_id',
        'expense_type'
    ]
    key_info = {
        'hidden': {'budget_id', 'expense_type_id'},
        'readonly': {'budget', 'expense_type'},
        'translate': {'_self'}
    }

# Caches to accelerate the performance of the application
class CacheTimestamp(Base):
    __tablename__ = 'cache_timestamp'

    table_name: Mapped[str] = mapped_column(primary_key=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime)

    def __str__(self) -> str:
        return f'{self.table_name} - {self.last_updated}'
    
class BrokerageAccountExternalTransaction(Base, Cache):
    __tablename__ = 'brokerage_account_external_transaction'

    account_id: Mapped[int] = mapped_column(ForeignKey('brokerage_account.id'), primary_key=True)
    record_date: Mapped[date] = mapped_column(Date, primary_key=True)
    market_value: Mapped[float] = mapped_column(default=0.0)
    investment: Mapped[float] = mapped_column(default=0.0)
    redemption: Mapped[float] = mapped_column(default=0.0)
    xirr: Mapped[float] = mapped_column(default=0.0)
    @property
    def profit(self) -> float:
        return self.redemption + self.market_value - self.investment
    def profit_rate(self) -> float:
        if self.investment == 0.0:
            return 0.0
        return self.profit / self.investment

    account: Mapped['BrokerageAccount'] = relationship(lazy='selectin')
    @classmethod
    def init_cache(cls, db_session: Session) -> None:
        """
        Initialize the cache for external brokerage account transactions.
        """
        max_date = db_session.scalar(select(func.max(cls.record_date)))
        models = db_session.scalars(select(BrokerageAccount)).all()
        for model in models:
            related_account_ids = [a.id for a in model.related_accounts]
            related_asset_ids = [a.id for a in model.related_assets]
            account_ex = aliased(HistoryExRate, name='account_ex')
            asset_ex = aliased(HistoryExRate, name='asset_ex')
            broker_acct_ex = aliased(HistoryExRate, name='broker_acct_ex')
            stmt = (
                select(
                    AccountTransaction.transaction_date.label('record_date'),
                    func.sum(
                        case(
                            (
                                and_(
                                    broker_acct_ex.currency_code != None,
                                    account_ex.currency_code != None,
                                    broker_acct_ex.ex_rate != None,
                                    account_ex.ex_rate != None,
                                    broker_acct_ex.currency_code != account_ex.currency_code,
                                    broker_acct_ex.ex_rate != 0.0
                                ),
                                AccountTransaction.amount_change * account_ex.ex_rate / broker_acct_ex.ex_rate
                            ), else_ = AccountTransaction.amount_change
                        )
                    ).label('cashflow'),
                    func.sum(
                        case(
                            (
                                and_(
                                    broker_acct_ex.currency_code != None,
                                    asset_ex.currency_code != None,
                                    broker_acct_ex.ex_rate != None,
                                    asset_ex.ex_rate != None,
                                    broker_acct_ex.currency_code != asset_ex.currency_code,
                                    broker_acct_ex.ex_rate != 0.0
                                ),
                                HistoryAccuAssetTransaction.market_value * asset_ex.ex_rate / broker_acct_ex.ex_rate
                            ), else_ = HistoryAccuAssetTransaction.market_value
                        )
                    ).label('market_value_change')
                )
                .join(Account, AccountTransaction.account_id == Account.id)
                .join(AssetTransaction, AccountTransaction.id == AssetTransaction.id, isouter=True)
                .join(Asset, AssetTransaction.asset_id == Asset.id, isouter=True)
                .join(
                    HistoryAccuAssetTransaction, 
                    and_(
                        AssetTransaction.asset_id == HistoryAccuAssetTransaction.asset_id,
                        AccountTransaction.transaction_date == HistoryAccuAssetTransaction.record_date
                    ), isouter=True
                )
                .join(
                    account_ex, 
                    and_(
                        AccountTransaction.transaction_date == account_ex.ex_date,
                        Account.currency_code == account_ex.currency_code
                    ), isouter=True
                )
                .join(asset_ex,
                    and_(
                        AssetTransaction.transaction_date == asset_ex.ex_date,
                        Asset.currency_code == asset_ex.currency_code
                    ), isouter=True
                )
                .join(broker_acct_ex,
                    and_(
                        AccountTransaction.transaction_date == broker_acct_ex.ex_date,
                        broker_acct_ex.currency_code == model.currency_code
                    ), isouter=True
                )
                .where(
                    or_(
                        and_(
                            AccountTransaction.account_id.in_(related_account_ids),
                            AccountTransaction.transaction_type != AccountTransactionType.ASSET_TRANSACTION
                        ),
                        and_(
                            AssetTransaction.asset_id.in_(related_asset_ids),
                            AccountTransaction.transaction_type == AccountTransactionType.ASSET_TRANSACTION,
                            ~AccountTransaction.account_id.in_(related_account_ids)
                        )
                    ),
                    AccountTransaction.transaction_date > max_date,
                )
                .group_by(
                    AccountTransaction.transaction_date
                )
                .order_by(
                    AccountTransaction.transaction_date
                )
            )
            ext_trans = db_session.execute(stmt).all()
            stmt = (
                select(
                    cls.record_date,
                    cls.investment,
                    cls.redemption,
                    cls.market_value
                )
                .where(
                    cls.account_id == model.id
                )
            )
            last_existing_trans = db_session.execute(stmt.order_by(cls.record_date.desc())).first()
            flows: list[tuple[date, float]] = []
            mv = 0.0
            investment = 0.0
            redemption = 0.0
            if last_existing_trans:
                rd, investment, redemption, market_value = last_existing_trans
                mv = market_value
                investment = investment
                redemption = redemption
            for rd, cf, mvc in existing_trans:
                if cf < 0.0:
                    investment += cf
                else:
                    redemption += cf
                mv += mvc
                flows.append((rd, cf + mvc))
            for account_id, rd, cf, mvc in ext_trans:
                mv += mvc
                flows.append((rd, cf + mv))
                cur_xirr = xirr(flows)
                db_session.execute(
                    update(cls)
                    .where(
                        and_(
                            cls.account_id == account_id,
                            cls.record_date == rd
                        )
                    )
                    .values(
                        investment=investment,
                        redemption=redemption,
                        xirr=cur_xirr
                    )
                )
            db_session.flush()
        db_session.commit()
        
    @classmethod
    def update_cache(cls, 
                     db_session: Session, 
                     account_ids: Iterable[int] | None = None,
                     record_date: date | None = None
    ) -> bool:
        """
        Update the cache for historical asset prices.
        """
        sub_q = (
            select(
                AssetTransaction.account_id.label('acct_id'),
                AssetTransaction.transaction_date.label('record_date')
            )
        )
        if record_date:
            sub_q = sub_q.where(AssetTransaction.transaction_date >= record_date)
        if account_ids:
            sub_q = sub_q.where(AssetTransaction.asset_id.in_(account_ids))
        sub_q = sub_q.distinct().subquery()
        agg_q = (
            select(
                sub_q.c.asset_id,
                sub_q.c.record_date,
                func.sum(
                    case(
                        (AssetTransaction.amount_change < 0.0, -AssetTransaction.amount_change), 
                        else_ = 0.0
                    )
                ).label('investment'),
                func.sum(
                    case(
                        (AssetTransaction.amount_change > 0.0, AssetTransaction.amount_change),
                        else_ = 0.0
                    )
                ).label('redemption'),
                func.sum(AssetTransaction.market_value_change).label('market_value'),
                func.sum(AssetTransaction.quantity_change).label('quantity')
            )
            .select_from(sub_q)
            .join(AssetTransaction, and_(
                sub_q.c.asset_id == AssetTransaction.asset_id,
                AssetTransaction.transaction_date <= sub_q.c.record_date
                )
            )
            .group_by(sub_q.c.asset_id, sub_q.c.record_date)
        )
        stmt = (
            insert(HistoryAccuAssetTransaction)
            .prefix_with("OR REPLACE")
            .from_select(
                [
                    HistoryAccuAssetTransaction.asset_id,
                    HistoryAccuAssetTransaction.record_date,
                    HistoryAccuAssetTransaction.investment,
                    HistoryAccuAssetTransaction.redemption,
                    HistoryAccuAssetTransaction.market_value,
                    HistoryAccuAssetTransaction.quantity
                ],
                agg_q
            )
            .returning(
                HistoryAccuAssetTransaction
            )
        )
        instances = db_session.scalars(stmt).all()
        for instance in instances:
            if isinstance(instance.asset, PublicStock) and instance.asset.code:
                stock_price = get_stock_price(instance.asset.code, instance.record_date)
                if stock_price:
                    instance.unit_price = stock_price
                    instance.market_value = stock_price * instance.quantity
            elif instance.quantity:
                instance.unit_price = instance.market_value / instance.quantity
            flows_stmt = (
                select(AssetTransaction.transaction_date, AssetTransaction.amount_change)
                .where(
                    AssetTransaction.asset_id == instance.asset_id,
                    AssetTransaction.transaction_date <= instance.record_date
                )
                .order_by(AssetTransaction.transaction_date)
            )
            flows = [(r.transaction_date, r.amount_change) for r in db_session.execute(flows_stmt)]
            flows.append((instance.record_date, instance.market_value))
            instance.xirr = xirr(flows)
        try:
            db_session.flush()
            return True
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error updating cache of HistoryAccuAssetTransaction: {e}")
            return False   
  

class HistoryExRate(Base, Cache):
    __tablename__ = 'history_ex_rate'
    ex_date: Mapped[date] = mapped_column(Date, primary_key=True)
    currency_code: Mapped[str] = mapped_column(ForeignKey('currency.code'), primary_key=True)
    ex_rate: Mapped[float] = mapped_column(default=1.0)
    currency: Mapped['Currency'] = relationship(lazy='selectin')
    @classmethod
    def init_cache(cls, db_session: Session) -> None:
        """
        Initialize the cache for historical exchange rates.
        """
        # Get the maximum date from the existing records
        last_udpated = db_session.scalar(
            select(CacheTimestamp.last_updated)
            .where(CacheTimestamp.table_name == cls.__tablename__)
        )
        stmt = select(AccountTransaction)
        if last_udpated:
            stmt = stmt.where(AccountTransaction.created_at > last_udpated)

        new_transactions = db_session.scalars(stmt).all()
        if not cls.update_cache(db_session, new_transactions):
            raise DatabaseError("Failed to update cache for HistoryExRate")

    @classmethod
    def update_cache(cls, db_session: Session, transactions: Iterable[AccountTransaction]) -> bool:
        code_dates: set[tuple[str, date]] = set()
        for t in transactions:
            dt = t.transaction_date
            if isinstance(t, AssetTransaction):
                code_dates.add((t.asset.currency_code, dt))
                if t.account_id != t.asset.brokerage_account_id:
                    if t.account.currency_code:
                        code_dates.add((t.account.currency_code, dt))
                    if t.asset.brokerage_account.currency_code:
                        code_dates.add((t.asset.brokerage_account.currency_code, dt))
            elif isinstance(t, AccountTransaction):
                acc = t.account
                while(acc.parent_account):
                    acc = acc.parent_account
                    if isinstance(acc, BrokerageAccount) and acc.currency_code:
                        code_dates.add((acc.currency_code, dt))
            stmt = (
                select(HistoryExRate.currency_code, HistoryExRate.ex_date)
                .where(
                    tuple_(HistoryExRate.currency_code, HistoryExRate.ex_date).in_(code_dates)
                )
            )
            existing_rows = db_session.execute(stmt).all()
            existing_code_dates = {(er_code, er_date) for er_code, er_date in existing_rows}
            code_dates = code_dates - existing_code_dates
            values = []
            try:
                for c, dt in code_dates:
                    if c == 'USD':
                        continue
                    r = get_stock_price(f'{c}USD=X', dt)
                    if r:
                        values.append({
                            'currency_code': c,
                            'ex_date': dt,
                            'ex_rate': r
                        })
                # Insert the new exchange rates into the history exchange rate table
                if values:
                    db_session.execute(
                        insert(HistoryExRate)
                            .prefix_with("OR REPLACE")
                            .values(values)
                    )
                db_session.flush()
                return True
            except Exception as e:
                db_session.rollback()
                logger.error(f"Error updating cache of HistoryExRate: {e}")
                return False
   
class HistoryAccuAssetTransaction(Base, Cache):
    __tablename__ = 'history_accu_asset_transaction'

    asset_id: Mapped[int] = mapped_column(ForeignKey('asset.id'), primary_key=True)
    record_date: Mapped[date] = mapped_column(Date, primary_key=True)
    investment: Mapped[float] = mapped_column(default=0.0)
    redemption: Mapped[float] = mapped_column(default=0.0)
    market_value: Mapped[float] = mapped_column(default=0.0)
    quantity: Mapped[float] = mapped_column(default=0.0)
    unit_price: Mapped[float] = mapped_column(default=0.0)
    @property
    def profit(self) -> float:
        return self.market_value + self.redemption - self.investment
    @property
    def profit_rate(self) -> float:
        if self.investment == 0:
            return 0.0
        return self.profit / self.investment
    xirr: Mapped[float] = mapped_column(default=0.0)
    asset: Mapped['Asset'] = relationship(
        back_populates='accu_transactions', 
        lazy='selectin'
    )

    data_list = [
        'asset_id',
        'asset',
        'record_date',
        'investment',
        'redemption',
        'market_value',
        'unit_price',
        'quantity',
        'profit',
        'profit_rate',
        'xirr'
    ]
    key_info = {
        'hidden': {'asset_id'},
        'readonly': {'asset', 'profit', 'profit_rate', 'xirr'}
    }

    def __str__(self) -> str:
        return f'{self.asset} @ {self.record_date} = {self.market_value} {self.asset.currency_code}'
    
    def update_self_cache(self) -> bool:
        """
        Update the cache for historical asset prices.
        """
        db_session = Session.object_session(self)
        if not db_session:
            raise ValueError("No active session found for CacheMixin.update_cache")
        return HistoryAccuAssetTransaction.update_cache(db_session, [self.asset_id], self.record_date)
    @classmethod
    def init_cache(cls, db_session: Session) -> None:
        """
        Initialize the cache for historical asset prices.
        """
        sub_q = (
            select(cls.asset_id, func.max(cls.record_date).label('max_date'))
            .group_by(cls.asset_id)
            .subquery()
        )
        stmt = (
            select(AssetTransaction.asset_id, func.min(AssetTransaction.transaction_date))
            .join(sub_q, AssetTransaction.asset_id == sub_q.c.asset_id, isouter=True)
            .where(or_(
                AssetTransaction.transaction_date > sub_q.c.max_date,
                sub_q.c.max_date == None
            ))
            .group_by(AssetTransaction.asset_id)
        )
        result = db_session.execute(stmt).all()
        for asset_id, record_date in result:
            if not cls.update_cache(db_session, [asset_id], record_date):
                logger.error(f"Failed to initialize cache for asset {asset_id} on {record_date}")
        
    @classmethod
    def update_cache(cls, 
                     db_session: Session, 
                     asset_ids: Iterable[int] | None = None,
                     record_date: date | None = None
    ) -> bool:
        """
        Update the cache for historical asset prices.
        """
        sub_q = (
            select(
                AssetTransaction.asset_id.label('asset_id'),
                AssetTransaction.transaction_date.label('record_date')
            )
        )
        if record_date:
            sub_q = sub_q.where(AssetTransaction.transaction_date >= record_date)
        if asset_ids:
            sub_q = sub_q.where(AssetTransaction.asset_id.in_(asset_ids))
        sub_q = sub_q.distinct().subquery()
        agg_q = (
            select(
                sub_q.c.asset_id,
                sub_q.c.record_date,
                func.sum(
                    case(
                        (AssetTransaction.amount_change < 0.0, -AssetTransaction.amount_change), 
                        else_ = 0.0
                    )
                ).label('investment'),
                func.sum(
                    case(
                        (AssetTransaction.amount_change > 0.0, AssetTransaction.amount_change),
                        else_ = 0.0
                    )
                ).label('redemption'),
                func.sum(AssetTransaction.market_value_change).label('market_value'),
                func.sum(AssetTransaction.quantity_change).label('quantity')
            )
            .select_from(sub_q)
            .join(AssetTransaction, and_(
                sub_q.c.asset_id == AssetTransaction.asset_id,
                AssetTransaction.transaction_date <= sub_q.c.record_date
                )
            )
            .group_by(sub_q.c.asset_id, sub_q.c.record_date)
        )
        stmt = (
            insert(HistoryAccuAssetTransaction)
            .prefix_with("OR REPLACE")
            .from_select(
                [
                    HistoryAccuAssetTransaction.asset_id,
                    HistoryAccuAssetTransaction.record_date,
                    HistoryAccuAssetTransaction.investment,
                    HistoryAccuAssetTransaction.redemption,
                    HistoryAccuAssetTransaction.market_value,
                    HistoryAccuAssetTransaction.quantity
                ],
                agg_q
            )
            .returning(
                HistoryAccuAssetTransaction
            )
        )
        instances = db_session.scalars(stmt).all()
        try:
            for instance in instances:
                if isinstance(instance.asset, PublicStock) and instance.asset.code:
                    stock_price = get_stock_price(instance.asset.code, instance.record_date)
                    if stock_price:
                        instance.unit_price = stock_price
                        instance.market_value = stock_price * instance.quantity
                elif instance.quantity:
                    instance.unit_price = instance.market_value / instance.quantity
                flows_stmt = (
                    select(AssetTransaction.transaction_date, AssetTransaction.amount_change)
                    .where(
                        AssetTransaction.asset_id == instance.asset_id,
                        AssetTransaction.transaction_date <= instance.record_date
                    )
                    .order_by(AssetTransaction.transaction_date)
                )
                flows = [(r.transaction_date, r.amount_change) for r in db_session.execute(flows_stmt)]
                flows.append((instance.record_date, instance.market_value))
                instance.xirr = xirr(flows)
            db_session.flush()
            return True
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error updating cache of HistoryAccuAssetTransaction: {e}")
            return False   
    
@event.listens_for(Session, 'after_flush')
def _refresh_cache(session: Session, flush_context) -> None:
    """
    Refresh the history exchange rate cache after each flush.
    """
    touched = any(
        isinstance(obj, AssetTransaction)
        for obj in session.new | session.dirty
    )
    if touched:
        if not HistoryAccuAssetTransaction.update_cache(session):
            logger.warning("Failed to update history asset transaction cache.")
        if not HistoryExRate.update_cache(session):
            logger.warning("Failed to update history exchange rate cache.")
