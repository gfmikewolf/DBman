import csv
import io
from typing import Any
from flask import Response, jsonify, request
from werkzeug.datastructures import FileStorage
from sqlalchemy import Integer, String, Enum as SqlEnum, ForeignKey, delete, literal_column, Date, insert
from datetime import date as python_date, datetime
from sqlalchemy.orm import mapped_column, Mapped, synonym, relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from ..base import Base
from .types import AccountType, Gender

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
    owner_id: Mapped[int] = mapped_column(ForeignKey('manager.id'))
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
            'account_number',
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
            'organization',
            'parent_id',
            'parent_account'
        ),
        'hidden': {'id', 'owner_id', 'organization_id', 'currency_code', 'parent_id'},
        'readonly': {'id', 'owner', 'organization', 'currency', 'parent_account'}
    }

    __mapper_args__ = {
        'polymorphic_identity': AccountType.LOAN_ACCOUNT,
    }

class Expense(Base):
    __tablename__ = 'expense'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[python_date] = mapped_column(Date, default=python_date.today)
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
        return f'{self.date} {self.amount} {self.currency_code}'
    
    @_name.expression
    def _name(cls):
        return (literal_column("expense.date") + ' ' + literal_column("expense.amount") + ' ' + literal_column("expense.currency_code")).cast(String)
    
    key_info = {
        'data': (
            'id',
            'date',
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
    def load_ADCB_account_statement(cls, db_session: Session, ADCB_account_statement: FileStorage) -> dict[str, Any]:
        stream = io.StringIO(ADCB_account_statement.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream, delimiter=',')
        rows_to_insert = []

        for row in reader:
            data = {}
            if 'date' in row and row['date']:
                try:
                    dt = datetime.strptime(row['date'], "%d/%m/%Y")
                    data['date'] = dt.date()
                except:
                    return {'success': False, 'error': 'Invalid date format'}

            if 'remarks' in row:
                data['remarks'] = row['remarks']
            if 'amount' in row and row['amount']:
                try:
                    data['amount'] = float(row['amount'])
                except:
                    return {'success': False, 'error': 'Invalid amount format'}
            rows_to_insert.append(data)

        for data in rows_to_insert:
            expense = Expense(**data)
            db_session.add(expense)
        try:    
            db_session.commit()
            return {'success': True, 'data': f'{len(rows_to_insert)} records inserted'}
        except Exception as e:
            db_session.rollback()
            return {'success': False, 'error': str(e)}
        
class BudgetMAPExpense(Base):
    __tablename__ = 'budget__map__expense'
    budget_id: Mapped[int] = mapped_column(ForeignKey('budget.id'), primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey('expense.id'), primary_key=True)
    budget: Mapped['Budget'] = relationship(lazy='selectin')
    expense: Mapped['Expense'] = relationship(lazy='selectin')
    
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
    start_date: Mapped[python_date] = mapped_column(Date)
    end_date: Mapped[python_date] = mapped_column(Date)

    _name = synonym('name')

    expenses: Mapped[list['Expense']] = relationship(
        back_populates='budgets',
        secondary='budget__map__expense',
        lazy='select',
    )

    key_info = {
        'data': (
            'id',
            'name',
            'keywords',
            'budget_total',
            'start_date',
            'end_date'
        ),
        'hidden': { 'id' },
        'readonly': {'id' },
        'translate': { '_name'}
    }

    @classmethod
    def update_budget(cls, db_session: Session) -> dict[str, Any]:
        """
        Update BudgetMAPExpense table for each budget when an expense fits the
        keywords (comm-separated) of the budget and between the start_date and
        end_date of the budget.
        """
        # Fetch all expenses
        expenses = db_session.query(Expense).filter(
            Expense.date >= Budget.start_date,
            Expense.date <= Budget.end_date
        ).all()
        budgets = db_session.query(Budget).filter(
            Budget.keywords != None,
            Budget.keywords != '',
        ).all()

        new_mappings = []

        for budget in budgets:
            keywords = [k.strip() for k in budget.keywords.split(",") if k.strip()] # type: ignore
            for expense in expenses:
                if expense.remarks and any(keyword.lower() in expense.remarks.lower() for keyword in keywords):
                    new_mappings.append({'budget_id':budget.id, 'expense_id':expense.id})
        try:
            db_session.execute(delete(BudgetMAPExpense))
            db_session.execute(insert(BudgetMAPExpense).values(new_mappings))
            db_session.commit()
            return {'success': True, 'data': f'{len(new_mappings)} records inserted'}
        except Exception as e:
            db_session.rollback()
            return {'success': False, 'error': str(e)}

        