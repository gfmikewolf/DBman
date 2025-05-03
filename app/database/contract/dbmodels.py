# app/database/contract/dbmodels.py
from bdb import effective
import logging

logger = logging.getLogger(__name__)
from datetime import date
from sqlalchemy import (
    ForeignKey, 
    Date, Integer, String, Enum as SqlEnum,
    func, 
    select,
    case,
    literal_column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from ..base import Base
from .types import ClausePos, ClauseType, ClauseAction, ExpiryType, Milestone
from ..user import User, UserRole

class Contract(Base):
    __tablename__ = 'contract'
    contract_id: Mapped[int] = mapped_column(primary_key = True, autoincrement = True)
    contract_name: Mapped[str]
    contract_fullname: Mapped[str | None]
    contract_remarks: Mapped[str | None]
    contract_number_huawei: Mapped[str | None]
    
    amendments: Mapped[list['Amendment']] = relationship(
        back_populates = 'contract', 
        lazy = 'select',
        order_by = lambda: Amendment.amendment_signdate
    )
    parent_contracts: Mapped[list['Contract']] = relationship(
        back_populates='child_contracts', 
        secondary=lambda: ContractMAPContract.__table__,
        primaryjoin=lambda: Contract.contract_id == ContractMAPContract.child_contract_id,
        secondaryjoin=lambda: Contract.contract_id == ContractMAPContract.parent_contract_id,
        lazy='select'
    )
    child_contracts: Mapped[list['Contract']] = relationship(
        back_populates='parent_contracts', 
        secondary=lambda: ContractMAPContract.__table__,
        primaryjoin=lambda: Contract.contract_id == ContractMAPContract.parent_contract_id,
        secondaryjoin=lambda: Contract.contract_id == ContractMAPContract.child_contract_id,
        lazy='select'
    )
    legal_parent_contracts: Mapped[list['Contract']] = relationship(
        back_populates='legal_child_contracts', 
        secondary=lambda: ContractLEGALMAPContract.__table__,
        primaryjoin=lambda: Contract.contract_id == ContractLEGALMAPContract.child_contract_id,
        secondaryjoin=lambda: Contract.contract_id == ContractLEGALMAPContract.parent_contract_id,
        lazy='select'
    )
    legal_child_contracts: Mapped[list['Contract']] = relationship(
        back_populates='legal_parent_contracts', 
        secondary=lambda: ContractLEGALMAPContract.__table__,
        primaryjoin=lambda: Contract.contract_id == ContractLEGALMAPContract.parent_contract_id,
        secondaryjoin=lambda: Contract.contract_id == ContractLEGALMAPContract.child_contract_id,
        lazy='select'
    )
    clauses: Mapped[list['Clause']] = relationship(
        lazy='select',
        secondary=lambda: Amendment.__table__
    )
    user_roles: Mapped[list['UserRole']] = relationship(
        secondary=lambda: UserRoleMAPContract.__table__,
        primaryjoin=lambda: Contract.contract_id == UserRoleMAPContract.contract_id,
        secondaryjoin=lambda: UserRoleMAPContract.user_role_id == UserRole.user_role_id,
        lazy='select'
    )

    @property
    def contract_signdate(self) -> date | None: # type: ignore
        dates = [am.amendment_signdate for am in self.amendments]
        if dates:
            return min(dates)
        return None
    
    @property
    def contract_effectivedate(self) -> date | None: # type: ignore
        if self.amendments:
            dates = [amendment.amendment_effectivedate for amendment in self.amendments]
            if dates:
                return min(dates)
        return None
    
    @property
    def contract_expirydate(self) -> date | None: # type: ignore
        stmt = (
            select(ClauseTermination.termination_date).join(Amendment)
            .order_by(Amendment.amendment_effectivedate.desc())
            .where(ClauseTermination.contract_id==self.contract_id)
        )
        db_sess = Session.object_session(self)
        if db_sess is None:
            logger.error('Session is required in calling contract_expirydate')
            return None
        t_date = db_sess.scalars(stmt).first()
        if t_date:
            return t_date
        else:
            return self._fetch_contract_expirydate(set())
    
    @property
    def entities(self) -> set['Entity']: # type: ignore
        new_set = set()
        old_set = set()
        for amendment in self.amendments:
            for clause in amendment.clauses:
                if clause.clause_type == ClauseType.CLAUSE_ENTITY:
                    new_one = getattr(clause, 'new_entity', None)
                    old_one = getattr(clause, 'old_entity', None)
                    if new_one:
                        new_set.add(new_one)
                    if (old_one):
                        old_set.add(old_one)
        return new_set - old_set

    @property
    def scopes(self) -> set['Scope']: # type: ignore
        new_set = set()
        old_set = set()
        for amendment in self.amendments:
            for clause in amendment.clauses:
                if clause.clause_type == ClauseType.CLAUSE_SCOPE:
                    new_one = getattr(clause, 'new_scope', None)
                    old_one = getattr(clause, 'old_scope', None)
                    if new_one:
                        new_set.add(new_one)
                    if (old_one):
                        old_set.add(old_one)
        return new_set - old_set

    commercial_incentives: Mapped[list['ClauseCommercialIncentive']] = relationship(
        secondary=lambda: Amendment.__table__,
        primaryjoin=lambda: Contract.contract_id == Amendment.contract_id,
        secondaryjoin=lambda: Amendment.amendment_id == ClauseCommercialIncentive.amendment_id,
        viewonly=True,
        lazy='select',
        order_by=lambda: Amendment.amendment_effectivedate.desc()
    )

    def __str__(self) -> str:
        return self.contract_name
    
    def _fetch_contract_expirydate(self, visited: set[int], event_date: date = date.today()) -> date | None:
        if self.contract_id in visited:
            logger.error(f'Circular reference detected for contract id: {self.contract_id}')
            return None
        visited.add(self.contract_id)
        db_sess = Session.object_session(self)
        amendments = None
        if db_sess is None:
            logger.error('Session is required in calling contract_expirydate')
            return None    
        stmt = select(Amendment).join(Contract).where(
            Amendment.amendment_signdate <= event_date,
            Amendment.amendment_effectivedate <= event_date,
            Amendment.contract_id == self.contract_id
        ).order_by(Amendment.amendment_signdate.desc())
        amendments = db_sess.scalars(stmt).all()
        if not amendments:
            return None
        for amendment in amendments: # sorted by signdate.desc
            for clause in amendment.clauses:
                if not isinstance(clause, ClauseExpiry):
                    continue
                if clause.expiry_type == ExpiryType.FD:
                    return clause.expiry_date
                elif clause.expiry_type == ExpiryType.LC:
                    linked_contract = clause.linked_to_contract
                    if linked_contract is None:
                        logger.error(f'Clause id:{clause.clause_id} expiry type is LC but no contract is linked')
                        return None
                    return linked_contract._fetch_contract_expirydate(visited, event_date)
                elif clause.expiry_type == ExpiryType.LL:
                    expiry_date = clause.expiry_date
                    for child_contract in self.child_contracts:
                        child_expiry_date = child_contract._fetch_contract_expirydate(visited, event_date)
                        if child_expiry_date is None:
                            logger.error(f'Contract id: {child_contract.contract_id} missing expiry_date')
                            return None
                        if expiry_date is None or child_expiry_date > expiry_date :
                            expiry_date = child_expiry_date
                    return expiry_date
                else:
                    logger.error(f'Clause id {clause.clause_id} wrong expiry_type {clause.expiry_type}')
                    return None

    key_info = {
        'data': [
            'contract_name',
            'contract_fullname',
            'contract_effectivedate',
            'contract_expirydate',
            'contract_signdate',
            'contract_remarks',
            'contract_number_huawei',
            'entities',
            'scopes'
        ],
        'readonly': {
            'contract_effectivedate',
            'contract_expirydate',
            'contract_signdate',
            'entities',
            'scopes'
        },
        'viewable_list': {
            'scope_reprs',
            'clauses',
            'amendments',
            'parent_contracts',
            'child_contracts',
            'legal_parent_contracts',
            'legal_child_contracts'
        },
        '_rv_admin': {
            'user_roles'
        },
        'longtext': { 'contract_fullname', 'contract_remarks' }
    }

class Amendment(Base):
    __tablename__ = 'amendment'
    amendment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amendment_name: Mapped[str]
    amendment_fullname: Mapped[str|None]
    amendment_signdate: Mapped[date] = mapped_column(Date)
    amendment_effectivedate: Mapped[date] = mapped_column(Date)
    amendment_remarks: Mapped[str|None]
    contract_id: Mapped[int] = mapped_column(ForeignKey('contract.contract_id'))
    amendment_number_huawei: Mapped[str|None]

    contract: Mapped['Contract'] = relationship(
        back_populates='amendments', 
        lazy='selectin',
        info={
            'order_by': (Contract.contract_name,)
        }
    )

    clauses: Mapped[list['Clause']] = relationship(
        back_populates='amendment',
        lazy = 'select'
    )
    
    def __str__(self) -> str:
        return f'{self.amendment_name} @ {self.amendment_effectivedate}'

    key_info = {
        'data': [
            'amendment_name',
            'contract_id',
            'contract',
            'amendment_fullname',
            'amendment_signdate',
            'amendment_effectivedate',
            'amendment_remarks',
            'amendment_number_huawei'
        ],
        'hidden': {'contract_id'},
        'readonly': {'contract'},
        'viewable_list': {'clauses'},
        'longtext': {'amendment_remarks'}
    }

class Entitygroup(Base):
    __tablename__ = 'entitygroup'
    entitygroup_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entitygroup_name: Mapped[str]

    entities: Mapped[list['Entity']] = relationship(
        back_populates='entitygroup',
        lazy='select'
    )

    def __str__(self):
        return self.entitygroup_name
    
    key_info = {
        'data': [
            'entitygroup_name'
        ],
        'translate': { '_self', 'entitygroup_name' }
    }

class Entity(Base):
    __tablename__ = 'entity'
    entity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_name: Mapped[str]
    entity_fullname: Mapped[str | None]
    entity_address: Mapped[str | None]
    remarks: Mapped[str | None]
    entitygroup_id: Mapped[int] = mapped_column(ForeignKey('entitygroup.entitygroup_id'))

    entitygroup: Mapped['Entitygroup'] = relationship(
        back_populates='entities',
        lazy='selectin',
        info={'order_by': (Entitygroup.entitygroup_name,)},
    )
    def __str__(self):
        return self.entity_name
    
    key_info = {
        'data': [
            'entity_name',
            'entity_fullname',
            'entitygroup_id',
            'entitygroup',
            'entity_address'
        ],
        'hidden': {'entitygroup_id'},
        'readonly': {'entitygroup'},
        'longtext': {'entity_address', 'entity_fullname'},
        'translate': {'_self', 'entity_name'}
    }

class Scope(Base):
    __tablename__ = 'scope'
    scope_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope_name: Mapped[str]
    remarks: Mapped[str | None]
    
    parent_scopes: Mapped[list['Scope']] = relationship(
        back_populates='child_scopes', 
        secondary=lambda: ScopeMAPScope.__table__,
        primaryjoin=lambda: Scope.scope_id == ScopeMAPScope.child_scope_id,
        secondaryjoin=lambda: Scope.scope_id == ScopeMAPScope.parent_scope_id,
        lazy='select'
    )
    child_scopes: Mapped[list['Scope']] = relationship(
        back_populates='parent_scopes', 
        secondary=lambda: ScopeMAPScope.__table__,
        primaryjoin=lambda: Scope.scope_id == ScopeMAPScope.parent_scope_id,
        secondaryjoin=lambda: Scope.scope_id == ScopeMAPScope.child_scope_id,
        lazy='select'
    )
    
    def __str__(self):
        return self.scope_name
    
    key_info = {
        'data': ['scope_name', 'parent_scopes', 'child_scopes', 'remarks'],
        'readonly': {'parent_scopes', 'child_scopes'},
        'longtext': {'remarks'},
        'translate': {'_self', 'scope_name'}
    }

class ScopeMAPScope(Base):
    __tablename__ = 'scope__map__scope'
    parent_scope_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('scope.scope_id'),
        primary_key=True
    )
    child_scope_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('scope.scope_id'),
        primary_key=True
    )
    parent_scope: Mapped['Scope'] = relationship(
        foreign_keys=[parent_scope_id],
        lazy = 'selectin',
        overlaps='parent_scopes, child_scopes'
    )
    child_scope: Mapped['Scope'] = relationship(
        foreign_keys=[child_scope_id],
        lazy = 'selectin',
        overlaps='parent_scopes, child_scopes'
    )

    key_info = {
        'data': [
            'parent_scope_id',
            'parent_scope',
            'child_scope_id',
            'child_scope'
        ],
        'hidden': { 'parent_scope_id', 'child_scope_id' },
        'readonly': { 'parent_scope', 'child_scope' }
    }     
class ContractMAPContract(Base):
    __tablename__ = 'contract__map__contract'
    parent_contract_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('contract.contract_id'),
        primary_key=True
    )
    child_contract_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('contract.contract_id'),
        primary_key=True
    )
    parent_contract: Mapped['Contract'] = relationship(
        foreign_keys=[parent_contract_id],
        lazy = 'selectin',
        overlaps= 'parent_contracts, child_contracts'
    )
    child_contract: Mapped['Contract'] = relationship(
        foreign_keys=[child_contract_id],
        lazy = 'selectin',
        overlaps= 'parent_contracts, child_contracts'
    )
    def __str__(self):
        return f'{self.child_contract} ∈ {self.parent_contract}'
    key_info = {
        'data': [
            'parent_contract_id',
            'parent_contract',
            'child_contract_id',
            'child_contract'
        ],
        'hidden': { 'parent_contract_id', 'child_contract_id' },
        'readonly': { 'parent_contract', 'child_contract' }
    }  
class ContractLEGALMAPContract(Base):
    __tablename__ = 'contract__legal_map__contract'
    parent_contract_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('contract.contract_id'),
        primary_key=True
    )
    child_contract_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('contract.contract_id'),
        primary_key=True
    )
    parent_contract: Mapped['Contract'] = relationship(
        foreign_keys=[parent_contract_id],
        lazy = 'selectin',
        overlaps= 'legal_parent_contracts, legal_child_contracts'
    )
    child_contract: Mapped['Contract'] = relationship(
        foreign_keys=[child_contract_id],
        lazy = 'selectin',
        overlaps= 'legal_parent_contracts, legal_child_contracts'
    )

    def __str__(self):
        return f'{self.child_contract} ∈ {self.parent_contract}'
    key_info = {
        'data': [
            'parent_contract_id',
            'parent_contract',
            'child_contract_id',
            'child_contract'
        ],
        'hidden': { 'parent_contract_id', 'child_contract_id' },
        'readonly': { 'parent_contract', 'child_contract' }
    }  
class UserMAPScope(Base):
    __tablename__ = 'user__map__scope'
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id'), primary_key=True)
    scope_id: Mapped[int] = mapped_column(ForeignKey('scope.scope_id'), primary_key=True)
    from ..user import User
    user: Mapped['User'] = relationship(lazy='selectin')
    scope: Mapped['Scope'] = relationship(lazy='selectin')
    def __str__(self) -> str:
        return f'{self.user}:{self.scope}'
    key_info = {
        'data': ['user_id', 'user', 'scope_id', 'scope'],
        'hidden': {'user_id', 'scope_id'},
        'readonly': {'user', 'scope'}
    }
class UserRoleMAPContract(Base):
    __tablename__ = 'user_role__map__contract'
    user_role_id: Mapped[int] = mapped_column(ForeignKey('user_role.user_role_id'), primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey('contract.contract_id'), primary_key=True)

class Clause(Base):
    __tablename__ = 'clause'
    clause_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amendment_id: Mapped[int] = mapped_column(ForeignKey('amendment.amendment_id'))
    clause_pos: Mapped[ClausePos] = mapped_column(SqlEnum(ClausePos), default=ClausePos.M)
    clause_ref: Mapped[str | None]
    clause_type: Mapped[ClauseType] = mapped_column(SqlEnum(ClauseType))
    clause_text: Mapped[str | None]
    clause_reviewcomments: Mapped[str | None]
    clause_remarks: Mapped[str | None]
    effectivedate: Mapped[date|None] = mapped_column(Date)
    expirydate: Mapped[date|None] = mapped_column(Date)
    applied_to_scope_id: Mapped[int|None] = mapped_column(ForeignKey('scope.scope_id'))
    
    @property
    def clause_effective_date(self) -> date:
        return self.effectivedate or self.amendment.amendment_effectivedate
    
    @property
    def clause_expiry_date(self) -> date|None:
        return self.expirydate or self.amendment.contract.contract_expirydate
    
    applied_to_scope: Mapped['Scope'] = relationship(
        foreign_keys=[applied_to_scope_id],
        lazy='selectin',
        info={
            'order_by': lambda: Scope.scope_name
        }
    )

    amendment: Mapped['Amendment'] = relationship(
        back_populates='clauses',
        lazy='selectin',
        info={
            'order_by': Amendment.amendment_signdate
        }
    )   
    contract: Mapped['Contract'] = relationship(
        back_populates='clauses',
        secondary=lambda: Amendment.__table__,
        primaryjoin=lambda: Clause.amendment_id == Amendment.amendment_id,
        secondaryjoin=lambda: Contract.contract_id == Amendment.contract_id,
        viewonly=True,
        lazy='selectin'
    )
    def __str__(self) -> str:
        return f'{self.clause_type.value}'

    key_info = {
        'data': [
            'contract',
            'amendment',
            'amendment_id',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_text',
            'clause_reviewcomments',
            'clause_remarks',
            'effectivedate',
            'expirydate',
            'applied_to_scope_id',
            'applied_to_scope'  
        ],
        'hidden': { 'amendment_id', 'applied_to_scope_id' },
        'readonly': { 'amendment', 'contract', 'applied_to_scope' },
        'longtext': { 
            'clause_text', 
            'clause_reviewcomments', 
            'clause_remarks' 
        },
        'translate': { '_self' }
    }

    __mapper_args__ = {
        'polymorphic_on': clause_type,
        'polymorphic_identity': ClauseType.CLAUSE
    }
class ClauseTermination(Clause):
    __tablename__ = 'clause_termination'
    clause_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('clause.clause_id'),
        primary_key=True
    )
    contract_id: Mapped[int | None] = mapped_column(ForeignKey('contract.contract_id'))
    termination_date: Mapped[date] = mapped_column(Date)

    contract: Mapped[Contract] = relationship(lazy='selectin')

    def __str__(self) -> str:
        return f'{self.clause_type.name}: Contract [{self.contract}] @ {self.termination_date}'

    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_TERMINATION
    }

    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + ['contract_id', 'contract', 'termination_date'] # type: ignore
    key_info['hidden'] = key_info['hidden'] | {'contract_id'} # type: ignore
    key_info['readonly'] = key_info['readonly'] | {'contract'} # type: ignore
class ClauseScope(Clause):
    __tablename__ = 'clause_scope'
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
    clause_action: Mapped[ClauseAction] = mapped_column(
        SqlEnum(ClauseAction), 
        default=ClauseAction.A
    )
    
    new_scope_id: Mapped[int | None] = mapped_column(
        ForeignKey('scope.scope_id')
    )
    old_scope_id: Mapped[int | None] = mapped_column(
        ForeignKey('scope.scope_id'),
    )

    new_scope: Mapped['Scope'] = relationship(
        foreign_keys=[new_scope_id],
        lazy = 'selectin'
    )

    old_scope: Mapped['Scope'] = relationship(
        foreign_keys=[old_scope_id],
        lazy = 'selectin'
    )

    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_SCOPE
    }

    def __str__(self) -> str:
        nm = f'{self.clause_type.name}'
        if self.clause_action == ClauseAction.A:
            return nm + f' +[{self.new_scope}]'
        elif self.clause_action == ClauseAction.R:
            return nm + f' -[{self.old_scope}]'
        elif self.clause_action == ClauseAction.U:
            return nm + f' +[{self.new_scope}] -[{self.old_scope}]'
        else:
            return 'Wrong clause action type'

    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + [
        'clause_action', 'new_scope_id', 'new_scope', 'old_scope_id', 'old_scope'
    ] # type: ignore
    key_info['hidden'] = key_info['hidden'] | {'new_scope_id', 'old_scope_id'} # type: ignore
    key_info['readonly'] = key_info['readonly'] | {'new_scope', 'old_scope'} # type: ignore
class ClauseEntity(Clause):
    __tablename__ = 'clause_entity'
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
    clause_action: Mapped[ClauseAction] = mapped_column(
        SqlEnum(ClauseAction), 
        default=ClauseAction.A
    )
    new_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey('entity.entity_id')
    )
    old_entity_id: Mapped[int | None] = mapped_column(
        ForeignKey('entity.entity_id'),
    )
    new_entity: Mapped['Entity'] = relationship(
        foreign_keys=[new_entity_id],
        lazy = 'selectin'
    )
    old_entity: Mapped['Entity'] = relationship(
        foreign_keys=[old_entity_id],
        lazy = 'selectin'
    )

    def __str__(self) -> str:
        nm = f'{self.clause_type.name}'
        if self.clause_action == ClauseAction.A:
            return nm + f' +[{self.new_entity}]'
        elif self.clause_action == ClauseAction.R:
            return nm + f' -[{self.old_entity}]'
        elif self.clause_action == ClauseAction.U:
            return nm + f' +[{self.new_entity}] -[{self.old_entity}]'
        else:
            return 'Wrong clause action type'
    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_ENTITY
    }
    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + [
        'clause_action', 'new_entity_id', 'new_entity', 'old_entity_id', 'old_entity'
    ] # type: ignore
    key_info['hidden'] = key_info['hidden'] | {'new_entity_id', 'old_entity_id'} # type: ignore
    key_info['readonly'] = key_info['readonly'] | {'new_entity', 'old_entity'} # type: ignore
class ClauseExpiry(Clause):
    __tablename__ = 'clause_expiry'
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
    expiry_type: Mapped[ExpiryType] = mapped_column(SqlEnum(ExpiryType))
    expiry_date: Mapped[date | None] = mapped_column(Date)
    linked_to_contract_id: Mapped[int | None] = mapped_column(
        ForeignKey('contract.contract_id')
    )
    linked_to_contract: Mapped['Contract'] = relationship(
        lazy = 'selectin'
    )

    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_EXPIRY
    }

    def __str__(self) -> str:
        nm = f'{self.clause_type.name}: '
        nm += f'{self.expiry_type.value}: '
        if self.expiry_type in {ExpiryType.FD, ExpiryType.LL}:
            return nm + f'{self.expiry_date}'
        else:
            return nm + f'⇄{self.linked_to_contract}'

    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + [
        'expiry_type', 'expiry_date', 'linked_to_contract_id', 'linked_to_contract'
    ] # type: ignore
    key_info['hidden'] = key_info['hidden'] | {'linked_to_contract_id'} # type: ignore
    key_info['readonly'] = key_info['readonly'] | {'linked_to_contract'} # type: ignore
class ClauseCustomerList(Clause):
    __tablename__ = 'clause_customer_list'
    clause_action: Mapped[ClauseAction] = mapped_column(
        SqlEnum(ClauseAction), 
        default=ClauseAction.A
    )
    effective_date: Mapped[date | None] = mapped_column(Date)
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
    new_customer_id: Mapped[int | None] = mapped_column(
        ForeignKey('entity.entity_id')
    )
    old_customer_id: Mapped[int | None] = mapped_column(
        ForeignKey('entity.entity_id'),
    )
    new_customer: Mapped['Entity'] = relationship(
        foreign_keys=[new_customer_id],
        lazy = 'selectin'
    )
    old_customer: Mapped['Entity'] = relationship(
        foreign_keys=[old_customer_id],
        lazy = 'selectin'
    )

    def __str__(self) -> str:
        nm = f'{self.clause_type.name}'
        if self.clause_action == ClauseAction.A:
            return nm + f' +[{self.new_customer}]'
        elif self.clause_action == ClauseAction.R:
            return nm + f' -[{self.old_customer}]'
        elif self.clause_action == ClauseAction.U:
            return nm + f' +[{self.new_customer}] -[{self.old_customer}]'
        else:
            return 'Wrong clause action type'
    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_CUSTOMER_LIST
    }  
    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + [
        'clause_action', 'effective_date', 'new_customer_id', 'new_customer', 'old_customer_id', 'old_customer'
    ] # type: ignore
    key_info['hidden'] = key_info['hidden'] | {'new_customer_id', 'old_customer_id'} # type: ignore
    key_info['readonly'] = key_info['readonly'] | {'new_customer', 'old_customer'} # type: ignore
class ClauseDelete(Clause):
    __tablename__ = 'clause_delete'
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
    clause_to_delete_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id')
    )
    clause_to_delete: Mapped['Clause'] = relationship(
        foreign_keys=[clause_to_delete_id],
        lazy='selectin'
    )
    
    def __str__(self) -> str:
        return f'{self.clause_type.name} {self.clause_to_delete}'
    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_DELETE,
        'inherit_condition': clause_id == Clause.clause_id
    }  
    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + [
        'clause_to_delete_id', 'clause_to_delete'
    ] # type: ignore
    key_info['hidden'] = key_info['hidden'] | {'clause_to_delete_id'} # type: ignore
    key_info['readonly'] = key_info['readonly'] | {'clause_to_delete' } # type: ignore
class ClauseWarrantyPeriod(Clause):
    __tablename__ = 'clause_warranty_period'
    clause_id: Mapped[int] = mapped_column(ForeignKey('clause.clause_id'), primary_key=True)
    applied_to_scope_id: Mapped[int|None] = mapped_column(ForeignKey('scope.scope_id'))
    applied_to_scope: Mapped['Scope'] = relationship(lazy='selectin')
    start_from: Mapped[Milestone] = mapped_column(SqlEnum(Milestone))
    warranty_period_month: Mapped[int]
    def __str__(self) -> str:
        return f'{self.start_from.value} {self.warranty_period_month} months' + (' applied to {self.applied_to_scope}' if self.applied_to_scope else '')
    __mapper_args__ = { 'polymorphic_identity': ClauseType.CLAUSE_WARRANTY_PERIOD }
    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + [
        'applied_to_scope_id', 
        'applied_to_scope',
        'start_from',
        'warranty_period_month'
    ] # type: ignore
    key_info['hidden'] = key_info['hidden'] | {'applied_to_scope_id'} # type: ignore
    key_info['readonly'] = key_info['readonly'] | {'applied_to_scope'} # type: ignore
class ClauseCommercialIncentive(Clause):
    __tablename__ = 'clause_commercial_incentive'
    clause_id: Mapped[int] = mapped_column(ForeignKey('clause.clause_id'), primary_key=True)
    precondition: Mapped[str|None]
    offer: Mapped[str]
    def __str__(self) -> str:
        return f'{self.clause_type.value}' + (f' applied to {self.applied_to_scope}' if self.applied_to_scope else '')
    __mapper_args__ = { 'polymorphic_identity': ClauseType.CLAUSE_COMMERCIAL_INCENTIVE }
    key_info = Clause.key_info.copy()
    key_info['data'] = key_info['data'] + [
        'applied_to_scope_id', 
        'applied_to_scope',
        'precondition',
        'offer'
    ] # type: ignore
