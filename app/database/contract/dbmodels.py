# app/database/contract/dbmodels.py
from sqlalchemy import ForeignKey, Date, Integer, String, Enum as SqlEnum
from sqlalchemy.sql import literal_column
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date
from app.database.base import Base, DataJson, DataJsonType
from .clausetypes import ClausePos, ClauseType, ClauseAction

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

    _name = synonym('contract_name')

    amendments: Mapped[list['Amendment']] = relationship(
        back_populates='contract', 
        lazy='select', 
    )

    key_info = {
        'data': (
            'contract_id', 
            'contract_name', 
            'contract_fullname',
            'contract_effectivedate', 
            'contract_expirydate',
            'contract_scope', 
            'contract_entities', 
            'contract_remarks',
            'contract_number_huawei'
        ),
        'hidden': {'contract_id'},
        'readonly': {
            'contract_id', 
            'contract_effectivedate', 
            'contract_expirydate',
            'contract_scope',
            'contract_entities'
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
    
    _name = synonym('amendment_name')
 
    # 通常载入Amendment时，需要同时载入contract，所以lazy='selectin'
    contract: Mapped['Contract'] = relationship(
        back_populates='amendments', 
        lazy='selectin',
        info={'select_order': (Contract.contract_name,)},
    )

    # 载入Amendment时，未必需要载入clauses
    clauses: Mapped[list['Clause']] = relationship(
        back_populates='amendment',
        lazy = 'select'
    )

    key_info = {
        'data': (
            'amendment_id',
            'amendment_name',
            'contract_id',
            'contract',
            'amendment_fullname',
            'amendment_signdate',
            'amendment_effectivedate',
            'amendment_entities',
            'amendment_remarks'
        ),
        'hidden': {'amendment_id', 'contract_id'},
        'readonly': {'amendment_id', 'amendment_entities', 'contract'},
    }

class Clause(Base):
    __tablename__ = 'clause'
    clause_id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True)
    amendment_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('amendment.amendment_id'))
    clause_pos: Mapped[ClausePos] = mapped_column(
        SqlEnum(ClausePos), 
        default=ClausePos.MAINBODY)
    clause_ref: Mapped[str | None]
    clause_type: Mapped[ClauseType] = mapped_column(
        SqlEnum(ClauseType), 
        info={'DataJson_id_for': 'clause_json'}
    )
    clause_action: Mapped[ClauseAction] = mapped_column(
        SqlEnum(ClauseAction),
        default=ClauseAction.ADD)
    clause_json: Mapped[DataJson | None] = mapped_column(DataJsonType)
    clause_text: Mapped[str | None]
    clause_reviewcomments: Mapped[str | None]
    clause_remarks: Mapped[str | None]
    
    amendment: Mapped['Amendment'] = relationship(
        back_populates='clauses',
        lazy='selectin',
        info={'select_order': (Amendment.amendment_name,)}
    )

    @hybrid_property
    def _name(self) -> str: # type: ignore[override]
        return f"{self.clause_action.value}:{self.clause_type.value}:{self.clause_id}"
    
    @_name.expression
    def _name(cls):
        return (literal_column("clause_action") + ':' + 
                literal_column("clause_type") + '#' + 
                literal_column("clause_id")
               ).cast(String)
    
    key_info = {
        'data': (
            'clause_id',
            'amendment',
            'amendment_id',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_action',
            'clause_text',
            'clause_json',
            'clause_reviewcomments',
            'clause_remarks'  
        ),
        'hidden': { 'clause_id', 'amendment_id' },
        'readonly': { 'clause_id', 'amendment' },
        'longtext': { 'clause_text', 'clause_reviewcomments', 'clause_remarks' }
    }

class Entitygroup(Base):
    __tablename__ = 'entitygroup'
    entitygroup_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entitygroup_name: Mapped[str]

    _name = synonym('entitygroup_name')

    entities: Mapped[list['Entity']] = relationship(
        back_populates='entitygroup',
        lazy='select'
    )

    key_info = {
        'data': (
            'entitygroup_id',
            'entitygroup_name'
        ),
        'hidden': { 'entitygroup_id' },
        'readonly': { 'entitygroup_id' }
    }

class Entity(Base):
    __tablename__ = 'entity'
    entity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_name: Mapped[str]
    entity_fullname: Mapped[str | None]
    entitygroup_id: Mapped[int] = mapped_column(ForeignKey('entitygroup.entitygroup_id'))
    
    _name = synonym('entity_name')

    entitygroup: Mapped['Entitygroup'] = relationship(
        back_populates='entities',
        lazy='selectin',
        info={'select_order': (Entitygroup.entitygroup_name,)},
    )

    key_info = {
        'data': (
            'entity_id',
            'entity_name',
            'entity_fullname',
            'entitygroup_id',
            'entitygroup'
        ),
        'readonly': { 'entity_id' },
        'hidden': { 'entity_id', 'entitygroup_id' },
        'readonly': { 'entity_id', 'entitygroup' }
    }

class Scope(Base):
    __tablename__ = 'scope'
    scope_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope_name: Mapped[str]
    
    _name = synonym('scope_name')

    key_info = {
        'data': ( 'scope_id', 'scope_name' ),
        'hidden': { 'scope_id' },
        'readonly': { 'scope_id' }
    }
