# app/database/contract.py
from enum import Enum
from typing import List
from sqlalchemy import ForeignKey, Date,Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from datetime import date
from .base import Base, JsonBase

class Contract(Base):
    __tablename__ = 'contract'
    contract_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_name: Mapped[str] = mapped_column(String)
    contract_fullname: Mapped[str | None]
    contract_effectivedate: Mapped[date] = mapped_column(Date)
    contract_expirydate: Mapped[date] = mapped_column(Date)
    contract_scope: Mapped[str] = mapped_column()
    contract_entities: Mapped[str | None] = mapped_column()
    contract_remarks: Mapped[str | None]
    contract_number_huawei: Mapped[str | None]
    
    name = synonym('contract_name')
    
    amendments: Mapped[List['Amendment']] = relationship(
        back_populates='contract', 
        lazy='select', 
    )

    attr_info = {
        'pk': [contract_id],
        'hidden': [contract_id],
        'readonly': [
            contract_id, 
            contract_effectivedate, 
            contract_expirydate,
            contract_scope,
            contract_entities
        ],
        'required': [contract_name]
    }
    
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

class Amendment(Base):
    __tablename__ = 'amendment'
    amendment_id: Mapped[int] = mapped_column(primary_key=True)
    amendment_name: Mapped[str] = mapped_column(String)
    amendment_fullname: Mapped[str | None]
    amendment_signdate: Mapped[date] = mapped_column(Date)
    amendment_effectivedate: Mapped[date] = mapped_column(Date)
    amendment_entities: Mapped[str | None] = mapped_column(String)
    amendment_remarks: Mapped[str | None]
    contract_id: Mapped[int] = mapped_column(ForeignKey('contract.contract_id'))
    
    name = synonym('amendment_name')
 
    # 通常载入Amendment时，需要同时载入contract，所以lazy='selectin'
    contract: Mapped['Contract'] = relationship(
        back_populates='amendments', 
        lazy='selectin'
    )

    # 载入Amendment时，未必需要载入clauses
    clauses: Mapped['Clause'] = relationship(
        back_populates='amendment',
        lazy = 'select'
    )

    attr_info = {
        'pk': [amendment_id],
        'hidden': [amendment_id, contract_id],
        'readonly': [amendment_id, amendment_entities],
        'required': [
            amendment_name, 
            amendment_signdate, 
            amendment_effectivedate,
            contract_id
        ],
        'ref_map': {
            Contract: { Contract.contract_name: [Contract.contract_name] } # 合同id显示为合同名，按合同名正序排列
        }
    }

class ClauseType(Base):
    __tablename__ = 'clause_type'
    clause_type_id: Mapped[int] = mapped_column(primary_key=True)
    clause_type_name: Mapped[str] = mapped_column(String)

    name = synonym('clause_type_name')

    clauses: Mapped[List['Clause']] = relationship(
        back_populates='clause_type',
        lazy = 'select'
    )

    attr_info = {
        'pk': [clause_type_id],
        'hidden': [clause_type_id],
        'required': [clause_type_name],
        'readonly': [clause_type_id]
    }
    
class ClausePos(Base):
    __tablename__ = 'clause_pos'
    clause_pos_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clause_pos_name: Mapped[str] = mapped_column(String)

    attr_info = {
        'hidden': [clause_pos_id],
        'required': [clause_pos_name],
        'readonly': [clause_pos_id]
    }
 
    name = synonym('clause_pos_name')

    clauses: Mapped[List['Clause']] = relationship(
        back_populates='clause_pos',
        lazy = 'select'
    )

    attr_info = {
        'pk': [clause_pos_id],
        'hidden': [clause_pos_id],
        'required': [clause_pos_name],
        'readonly': [clause_pos_id]
    }

class ExpiryType(Enum):
    Date = 'Date'
    linked_to_Contract = 'linked_to_Contract'
    later_of_last_COA_or_Date = 'later_of_last_COA_or_Date'

class JsonClauseExpiry(JsonBase):
    expiry_type: ExpiryType
    expiry_date: date | None
    linked_contract_id: int | None
    attr_info = {
        'data_keys': ['expiry_type', 'expiry_date', 'linked_contract_id'],
        'required_keys': ['expiry_type'],
        'readonly_keys': []
    }

class Clause(Base):
    __tablename__ = 'clause'
    clause_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clause_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('clause_type.clause_type_id'))
    clause_ref: Mapped[str | None]
    clause_text: Mapped[str | None]
    amendment_id: Mapped[int] = mapped_column(Integer, ForeignKey('amendment.amendment_id'))
    clause_pos_id: Mapped[int] = mapped_column(Integer, ForeignKey('clause_pos.clause_pos_id'))
    clause_reviewcomments: Mapped[str | None]
    clause_remarks: Mapped[str | None]
    clause_effectivedate: Mapped[date | None] = mapped_column(Date)
    clause_expirydate: Mapped[date | None] = mapped_column(Date)
    clause_json: Mapped[dict] = mapped_column(JSON)
    clause_type: Mapped['ClauseType'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    id = synonym('clause_id')
    name = synonym('clause_text')

    amendment: Mapped['Amendment'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    clause_pos: Mapped['ClausePos'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    attr_info = {
        'hidden': [clause_id, clause_type_id, clause_pos_id],
        'readonly': [clause_id],
        'required': [clause_type_id, amendment_id, clause_pos_id, clause_json],
        'json_classes': {
            clause_json: {
                'identity_on': clause_type,
                'identity_attr': 'name',
                'classes_map': {
                    'expiry': JsonClauseExpiry
                }
            }
        },
        'ref_map': {
            ClauseType: { ClauseType.clause_type_name: [] },
            ClausePos: { ClausePos.clause_pos_name: [] },
            Amendment: { Amendment.amendment_name: [] }
        }
    }
