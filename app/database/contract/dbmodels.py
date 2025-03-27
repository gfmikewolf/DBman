# app/database/contract/dbmodels.py
from sqlalchemy import ForeignKey, Date, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from datetime import date
from app.database.base import Base, DataJson, DataJsonType
from .clausetypes import ClausePos, ClauseType

class Contract(Base):
    __tablename__ = 'contract'
    contract_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_name: Mapped[str]
    contract_fullname: Mapped[str | None]
    contract_effectivedate: Mapped[date | None] = mapped_column(Date)
    contract_expirydate: Mapped[date | None] = mapped_column(Date)
    contract_scope: Mapped[str | None]
    contract_entities: Mapped[str | None]
    contract_remarks: Mapped[str | None]
    contract_number_huawei: Mapped[str | None]

    name = synonym('contract_name')

    amendments: Mapped[list['Amendment']] = relationship(
        back_populates='contract', 
        lazy='select', 
    )

    col_key_info = {
        'hidden': {'contract_id'},
        'readonly': {
            'contract_id', 
            'contract_effectivedate', 
            'contract_expirydate',
            'contract_scope',
            'contract_entities'
        },
        'ref_name_order': {
            'contract_name': ('contract_name',)
        }
    }

class Amendment(Base):
    __tablename__ = 'amendment'
    amendment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amendment_name: Mapped[str]
    amendment_fullname: Mapped[str | None]
    amendment_signdate: Mapped[date] = mapped_column(Date)
    amendment_effectivedate: Mapped[date] = mapped_column(Date)
    amendment_entities: Mapped[str | None]
    amendment_remarks: Mapped[str | None] = mapped_column(String, info = {'longtext': True})
    contract_id: Mapped[int] = mapped_column(ForeignKey('contract.contract_id'))
    
    name = synonym('amendment_name')
 
    # 通常载入Amendment时，需要同时载入contract，所以lazy='selectin'
    contract: Mapped['Contract'] = relationship(
        back_populates='amendments', 
        lazy='selectin'
    )

    # 载入Amendment时，未必需要载入clauses
    clauses: Mapped[list['Clause']] = relationship(
        back_populates='amendment',
        lazy = 'select'
    )

    col_key_info = {
        'hidden': {'amendment_id', 'contract_id'},
        'readonly': {'amendment_id', 'amendment_entities'},
        'ref_name_order': {
            'contract_name': ('contract_name',)
        }
    }

class Clause(Base):
    __tablename__ = 'clause'
    clause_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clause_ref: Mapped[str | None] 
    clause_text: Mapped[str | None] 
    amendment_id: Mapped[int] = mapped_column(Integer, ForeignKey('amendment.amendment_id'))
    clause_reviewcomments: Mapped[str | None] = mapped_column(String, info = {'longtext': True}) 
    clause_remarks: Mapped[str | None] = mapped_column(String, info = {'longtext': True})
    clause_type: Mapped[ClauseType] = mapped_column(SqlEnum(ClauseType), info={'DataJson_id_for': 'clause_json'})
    clause_effectivedate: Mapped[date | None] = mapped_column(Date)
    clause_expirydate: Mapped[date | None] = mapped_column(Date)
    clause_pos: Mapped[ClausePos] = mapped_column(SqlEnum(ClausePos))
    clause_json: Mapped[DataJson] = mapped_column(DataJsonType)
    
    amendment: Mapped['Amendment'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    col_key_info = {
        'hidden': { 'clause_id', 'amendment_id' },
        'readonly': { 'clause_id' },
        'ref_name_order': {
            'amendment_name': ('contract_id', 'amendment_name')
        }
    }

class Entitygroup(Base):
    __tablename__ = 'entitygroup'
    entitygroup_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entitygroup_name: Mapped[str]

    name = synonym('entitygroup_name')

    entities: Mapped[list['Entity']] = relationship(
        back_populates='entitygroup',
        lazy='select'
    )

    col_key_info = {
        'hidden': { 'entitygroup_id' },
        'readonly': { 'entitygroup_id' }
    }

class Entity(Base):
    __tablename__ = 'entity'
    entity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_name: Mapped[str]
    entity_fullname: Mapped[str | None]
    entitygroup_id: Mapped[int] = mapped_column(ForeignKey('entitygroup.entitygroup_id'))
    
    name = synonym('entity_name')

    entitygroup: Mapped['Entitygroup'] = relationship(
        back_populates='entities',
        lazy='selectin'
    )

    col_key_info = {
        'hidden': { 'entity_id', 'entitygroup_id' },
        'readonly': { 'entity_id' },
        'ref_name_order': {
            'entitygroup_id': ('entitygroup_name',)
        }
    }

class Scope(Base):
    __tablename__ = 'scope'
    scope_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope_name: Mapped[str]
    
    name = synonym('scope_name')

    col_key_info = {
        'hidden': { 'scope_id' },
        'readonly': { 'scope_id' },
        'ref_name_order': {
            'scope_name': ('scope_name',)
        }
    }