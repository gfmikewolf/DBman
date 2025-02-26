# app/contract.py
from typing import List
from sqlalchemy import ForeignKey, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.orm import Session
from datetime import date
from .base_mixin import Base, ForeignKeyMixin, JSONMixin

class Amendment(ForeignKeyMixin, Base):
    __tablename__ = 'amendment'
    amendment_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden':True})
    amendment_name: Mapped[str]
    amendment_fullname: Mapped[str | None]
    amendment_signdate: Mapped[date] = mapped_column(Date)
    amendment_effectivedate: Mapped[date] = mapped_column(Date)
    amendment_entities: Mapped[str | None] = mapped_column(info={'readonly': True})
    amendment_remarks: Mapped[str | None]
    contract_id: Mapped[int] = mapped_column(
        ForeignKey('contract.contract_id'), 
        info={
            'rel_name': 'contract', 
            'fk_attr_name':'contract_name'
        }
    )
    
    id = synonym('amendment_id')
    name = synonym('amendment_name')
    
    contract: Mapped['Contract'] = relationship(
        back_populates='amendments', 
        lazy='selectin'
    )
    clauses: Mapped['Clause'] = relationship(
        back_populates='amendment',
        lazy = 'select'
    )

    @classmethod
    def get_options_fk(cls, session: Session):
        order_by_attr = {
            "contract": "contract_name",
        }
        return super().get_options_fk(session, order_by_attr=order_by_attr)

class Contract(Base):
    __tablename__ = 'contract'
    contract_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    contract_name: Mapped[str]
    contract_fullname: Mapped[str | None]
    contract_effectivedate: Mapped[date] = mapped_column(Date, info={'readonly': True})
    contract_expirydate: Mapped[date] = mapped_column(Date, info={'readonly': True})
    contract_scope: Mapped[str] = mapped_column(info={'readonly': True})
    contract_entities: Mapped[str | None] = mapped_column(info={'readonly': True})
    contract_remarks: Mapped[str | None]
    contract_number_huawei: Mapped[str | None]
    
    id = synonym('contract_id')
    name = synonym('contract_name')
    
    amendments: Mapped[List['Amendment']] = relationship(back_populates='contract', lazy='select')
    clauses_expiry: Mapped[List['ClauseExpiry']] = relationship(
        back_populates='contract',
        lazy='select'
    )

    def refresh_effective_date(self):
        related_amendments = self.amendments
        if related_amendments:
            effective_dates = [amendment.amendment_effectivedate for amendment in related_amendments]
            min_effective_date = min(effective_dates)
            self.contract_effectivedate = min_effective_date
    
    # unfinished
    def refresh_expiry_date(self, session):
        related_amendments = self.amendments
        if related_amendments:
            pass
    
class ClauseType(Base):
    __tablename__ = 'clause_type'
    clause_type_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    clause_type_name: Mapped[str]

    id = synonym('clause_type_id')
    name = synonym('clause_type_name')

    clauses: Mapped[List['Clause']] = relationship(
        back_populates='clause_type',
        lazy = 'select'
    )
    
class ClausePos(Base):
    __tablename__ = 'clause_pos'
    clause_pos_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    clause_pos_name: Mapped[str] = mapped_column(default='', nullable=False)

    id = synonym('clause_pos_id')
    name = synonym('clause_pos_name')

    clauses: Mapped[List['Clause']] = relationship(
        back_populates='clause_pos',
        lazy = 'select'
    )

class Clause(ForeignKeyMixin, Base):
    __tablename__ = 'clause'
    clause_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    clause_type_id: Mapped[int] = mapped_column(
        ForeignKey('clause_type.clause_type_id'),
        info={
            'rel_name': 'clause_type', 
            'fk_attr_name':'clause_type_name',
            'extension': True
        }
    )
    clause_ref: Mapped[str | None]
    clause_text: Mapped[str | None]
    amendment_id: Mapped[int] = mapped_column(
        ForeignKey('amendment.amendment_id'),
        info={
            'rel_name': 'amendment', 
            'fk_attr_name':'amendment_name'
        }
    )
    clause_pos_id: Mapped[int] = mapped_column(
        ForeignKey('clause_pos.clause_pos_id'),
        info={
            'rel_name': 'clause_pos', 
            'fk_attr_name':'clause_pos_name'
        }
    )
    clause_reviewcomments: Mapped[str | None]
    clause_remarks: Mapped[str | None]
    clause_effectivedate: Mapped[date | None] = mapped_column(Date)
    clause_expirydate: Mapped[date | None] = mapped_column(Date)

    amendment: Mapped['Amendment'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    clause_type: Mapped['ClauseType'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    clause_pos: Mapped['ClausePos'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    id = synonym('clause_id')
    name = synonym('clause_text')
    
    @classmethod
    def get_options_fk(cls, session: Session):
        order_by_attr = {
            "amendment": "amendment_name",
            "clause_type": "clause_type_name",
            "clause_pos": "clause_pos_name"
        }
        return super().get_options_fk(session, order_by_attr=order_by_attr)

class ClauseExpiry(ForeignKeyMixin, Base):
    __tablename__ = 'clause_expiry'
    clause_id: Mapped[int] = mapped_column(
        ForeignKey('clause.clause_id'),
        primary_key=True, 
        info={
            'rel_name': 'clause',
            'readonly': True, 
            'hidden': True
        }
    )
    expiry_type_id: Mapped[int] = mapped_column(
        ForeignKey('expiry_type.expiry_type_id'),
        info={
            'rel_name': 'expiry_type'
        }
    )
    expiry_date: Mapped[date] = mapped_column(Date)
    contract_id: Mapped[int] = mapped_column(
        ForeignKey('contract.contract_id'),
        info={
            'rel_name': 'contract'
        }
    )

    id = synonym('clause_id')
    name = synonym('expiry_type_id')

    expiry_type: Mapped['ExpiryType'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    contract: Mapped['Contract'] = relationship(
        back_populates='clauses_expiry',
        lazy='selectin'
    )

    clause: Mapped['Clause'] = relationship(
        lazy='select'
    )
    
class ExpiryType(Base):
    __tablename__ = 'expiry_type'
    expiry_type_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    expiry_type_name: Mapped[str]
    
    id = synonym('expiry_type_id')
    name = synonym('expiry_type_name')

    clauses: Mapped[List['ClauseExpiry']] = relationship(
        back_populates='expiry_type',
        lazy = 'select'
    )
    
EXTModel = {
    'expiry': ClauseExpiry
}
