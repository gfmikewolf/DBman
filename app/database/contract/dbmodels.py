# app/database/contract/dbmodels.py
from codecs import backslashreplace_errors
from datetime import date
from sqlalchemy import ForeignKey, Date, Integer, String, Enum as SqlEnum, Column, Table, func, select
from sqlalchemy.sql import literal_column
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.ext.hybrid import hybrid_property
from ..base import Base, DataJson
from ..types import DataJsonType
from .types import ClausePos, ClauseType, ClauseAction

class Contract(Base):
    __tablename__ = 'contract'
    contract_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_name: Mapped[str]
    contract_fullname: Mapped[str | None] = mapped_column(String, info={'longtext': True})
    contract_remarks: Mapped[str | None] = mapped_column(String, info={'longtext': True})
    contract_number_huawei: Mapped[str | None]

    _name = synonym('contract_name')

    @hybrid_property
    def contract_effectivedate(self) -> date | None: # type: ignore
        if self.amendments:
            dates = [amendment.amendment_effectivedate for amendment in self.amendments]
            if dates:
                return min(dates)
        return None

    @contract_effectivedate.expression
    def contract_effectivedate(cls):
        return (
            select(func.min(Amendment.amendment_effectivedate))
            .where(Amendment.contract_id == cls.contract_id)
            .scalar_subquery()
        )
    
    amendments: Mapped[list['Amendment']] = relationship(
        back_populates='contract', 
        lazy='select',
        order_by=lambda: Amendment.amendment_name
    )
    parent_contracts: Mapped[list['Contract']] = relationship(
        back_populates='child_contracts', 
        secondary=lambda: contract__map__contract,
        primaryjoin=lambda: Contract.contract_id == contract__map__contract.c.child_contract_id,
        secondaryjoin=lambda: Contract.contract_id == contract__map__contract.c.parent_contract_id,
        lazy='select'
    )
    child_contracts: Mapped[list['Contract']] = relationship(
        back_populates='parent_contracts', 
        secondary=lambda: contract__map__contract,
        primaryjoin=lambda: Contract.contract_id == contract__map__contract.c.parent_contract_id,
        secondaryjoin=lambda: Contract.contract_id == contract__map__contract.c.child_contract_id,
        lazy='select'
    )
    legal_parent_contracts: Mapped[list['Contract']] = relationship(
        back_populates='legal_child_contracts', 
        secondary=lambda: contract__legal_map__contract,
        primaryjoin=lambda: Contract.contract_id == contract__legal_map__contract.c.child_contract_id,
        secondaryjoin=lambda: Contract.contract_id == contract__legal_map__contract.c.parent_contract_id,
        lazy='select'
    )
    legal_child_contracts: Mapped[list['Contract']] = relationship(
        back_populates='legal_parent_contracts', 
        secondary=lambda: contract__legal_map__contract,
        primaryjoin=lambda: Contract.contract_id == contract__legal_map__contract.c.parent_contract_id,
        secondaryjoin=lambda: Contract.contract_id == contract__legal_map__contract.c.child_contract_id,
        lazy='select'
    )
    entities: Mapped[list['Entity']] = relationship(
        back_populates='contracts',
        secondary=lambda: contract__map__entity,
        lazy='select'
    )
    scopes: Mapped[list['Scope']] = relationship(
        back_populates='contracts',
        secondary=lambda: contract__map__scope,
        lazy='select'
    )
    clauses: Mapped[list['Clause']] = relationship(
        lazy='select',
        secondary=lambda: Amendment.__table__,
        primaryjoin=lambda: Contract.contract_id == Amendment.contract_id,
        secondaryjoin=lambda: Clause.amendment_id == Amendment.amendment_id,
        viewonly=True,
        order_by=lambda: Clause.clause_type
    )

    key_info = {
        'data': (
            'contract_id', 
            'contract_name',
            'contract_fullname',
            'contract_effectivedate',
            'contract_remarks',
            'contract_number_huawei',
            'entities'
        ),
        'hidden': {
            'contract_id'
        },
        'readonly': {
            'contract_id', 
            'contract_effectivedate',
            'entities'
        }
    }

class Amendment(Base):
    __tablename__ = 'amendment'
    amendment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amendment_name: Mapped[str]
    amendment_fullname: Mapped[str | None]
    amendment_signdate: Mapped[date] = mapped_column(Date)
    amendment_effectivedate: Mapped[date] = mapped_column(Date)
    amendment_remarks: Mapped[str | None] = mapped_column(String, info = {'longtext': True})
    contract_id: Mapped[int] = mapped_column(ForeignKey('contract.contract_id'))
    
    _name = synonym('amendment_name')
 
    contract: Mapped['Contract'] = relationship(
        back_populates='amendments', 
        lazy='selectin',
        info={'select_order': (Contract.contract_name,)},
    )

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
            'amendment_remarks'
        ),
        'hidden': {'amendment_id', 'contract_id'},
        'readonly': {'amendment_id', 'contract'},
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

    contract: Mapped['Contract'] = relationship(
        back_populates='clauses',
        secondary=lambda: Amendment.__table__,
        primaryjoin=lambda: Clause.amendment_id == Amendment.amendment_id,
        secondaryjoin=lambda: Contract.contract_id == Amendment.contract_id,
        viewonly=True,
        lazy='select'
    )

    @hybrid_property
    def _name(self) -> str: # type: ignore[override]
        return f"{self.clause_action.name}:{self.clause_type.name}#{self.clause_id}"
    
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

    contracts: Mapped[list['Contract']] = relationship(
        back_populates='entities',
        secondary=lambda: contract__map__entity,
        lazy='select'
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

    contracts: Mapped[list['Contract']] = relationship(
        back_populates='scopes',
        secondary=lambda: contract__map__scope,
        lazy='select'
    )

contract__map__contract = Table(
    'contract__map__contract',
    Base.metadata,
    Column('parent_contract_id', ForeignKey('contract.contract_id')),
    Column('child_contract_id', ForeignKey('contract.contract_id'))
)

contract__legal_map__contract = Table(
    'contract__legal_map__contract',
    Base.metadata,
    Column('parent_contract_id', ForeignKey('contract.contract_id')),
    Column('child_contract_id', ForeignKey('contract.contract_id'))
)

contract__map__entity = Table(
    'contract__map__entity',
    Base.metadata,
    Column('contract_id', ForeignKey('contract.contract_id')),
    Column('entity_id', ForeignKey('entity.entity_id'))
)

contract__map__scope = Table(
    'contract__map__scope',
    Base.metadata,
    Column('contract_id', ForeignKey('contract.contract_id')),
    Column('scope_id', ForeignKey('scope.scope_id'))
)
