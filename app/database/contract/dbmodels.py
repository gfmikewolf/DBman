# app/database/contract/dbmodels.py
from bdb import effective
import logging
from datetime import date, datetime
from sqlalchemy import (
    ForeignKey, 
    Date, Integer, String, Enum as SqlEnum,
    func, 
    select
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym, Session
from sqlalchemy.ext.hybrid import hybrid_property
from app.utils.common import _
from ..base import Base
from .types import ClausePos, ClauseType, ClauseAction, ExpiryType

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
    
    @property
    def contract_expirydate(self) -> date | None: # type: ignore
        stmt = select(ClauseTermination.termination_date).join(Amendment)
        stmt = stmt.order_by(Amendment.amendment_effectivedate.desc())
        stmt = stmt.where(ClauseTermination.contract_id==self.contract_id)
        db_sess = Session.object_session(self)
        if db_sess is None:
            logging.error('Session is required in calling contract_expirydate')
            return None
        t_date = db_sess.scalars(stmt).first()
        if t_date:
            return t_date
        else:
            return self._fetch_contract_expirydate(set())
    
    def _fetch_contract_expirydate(self, visited: set[int], event_date: date = datetime.today()) -> date | None:
        if self.contract_id in visited:
            logging.error(f'Circular reference detected for contract id: {self.contract_id}')
            return None
        visited.add(self.contract_id)
        db_sess = Session.object_session(self)
        amendments = None
        if db_sess is None:
            logging.error('Session is required in calling contract_expirydate')
            return None    
        stmt = select(Amendment).join(Contract).where(
            Amendment.amendment_signdate < event_date,
            Amendment.contract_id == self.contract_id
        ).order_by(Amendment.amendment_signdate.desc())
        result = db_sess.execute(stmt)
        amendments = result.scalars().all()
        if not amendments:
            return None
        for amendment in amendments: # sorted by signdate.desc
            for clause in amendment.clauses:
                if isinstance(clause, ClauseExpiry):
                    if clause.expiry_type == ExpiryType.FD and clause.applied_to_scope is None:
                        return clause.expiry_date
                    elif clause.expiry_type == ExpiryType.LC:
                        linked_contract = clause.linked_to_contract
                        if linked_contract is None:
                            logging.error(f'Clause id:{clause.clause_id} expiry type is LC but no contract is linked')
                            return None
                        return linked_contract._fetch_contract_expirydate(visited, event_date)
                    elif clause.expiry_type == ExpiryType.LL:
                        expiry_date = clause.expiry_date
                        if expiry_date is None:
                            logging.error(f'Clause id: {clause.clause_id} expiry type is LL but expiry_date is missing')
                            return None
                        for child_contract in self.child_contracts:
                            child_expiry_date = child_contract._fetch_contract_expirydate(visited, event_date)
                            if child_expiry_date is None:
                                logging.error(f'Contract id: {child_contract.contract_id} missing expiry_date')
                                return None
                            if child_expiry_date > expiry_date:
                                expiry_date = child_expiry_date
                        return expiry_date
                    else:
                        logging.error(f'Clause id {clause.clause_id} wrong expiry_type {clause.expiry_type}')
                        return None

    amendments: Mapped[list['Amendment']] = relationship(
        back_populates='contract', 
        lazy='select',
        order_by=lambda: Amendment.amendment_signdate
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
        secondary=lambda: Amendment.__table__,
        viewonly=True,
        order_by=lambda: Clause.clause_type
    )

    @hybrid_property
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

    @entities.expression
    def entities(cls):
        from .dbmodels import ClauseEntity, Amendment
        sub_old = (
            select(ClauseEntity.old_entity_id)
            .join(Amendment, Amendment.amendment_id == ClauseEntity.amendment_id)
            .where(
                Amendment.contract_id == cls.contract_id,
                ClauseEntity.old_entity_id.isnot(None)
            )
            .distinct()
        )
        new_expr = (
            select(func.group_concat(ClauseEntity.new_entity_id, ','))
            .join(Amendment, Amendment.amendment_id == ClauseEntity.amendment_id)
            .where(
                Amendment.contract_id == cls.contract_id,
                ClauseEntity.new_entity_id.isnot(None),
                ClauseEntity.new_entity_id.not_in(sub_old)
            )
            .distinct()
            .scalar_subquery()
        )
        return new_expr
    
    @hybrid_property
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

    @scopes.expression
    def scopes(cls):
        from .dbmodels import ClauseScope, Amendment
        sub_old = (
            select(ClauseScope.old_scope_id)
            .join(Amendment, Amendment.amendment_id == ClauseScope.amendment_id)
            .where(
                Amendment.contract_id == cls.contract_id,
                ClauseScope.old_scope_id.isnot(None)
            )
            .distinct()
        )
        new_expr = (
            select(func.group_concat(ClauseScope.new_scope_id, ','))
            .join(Amendment, Amendment.amendment_id == ClauseScope.amendment_id)
            .where(
                Amendment.contract_id == cls.contract_id,
                ClauseScope.new_scope_id.isnot(None),
                ClauseScope.new_scope_id.not_in(sub_old)
            )
            .distinct()
            .scalar_subquery()
        )
        return new_expr
    
    key_info = {
        'data': (
            'contract_id', 
            'contract_name',
            'contract_fullname',
            'contract_effectivedate',
            'contract_expirydate',
            'contract_remarks',
            'contract_number_huawei',
            'entities',
            'scopes'
        ),
        'hidden': {
            'contract_id'
        },
        'readonly': {
            'contract_id', 
            'contract_effectivedate',
            'contract_expirydate',
            'entities',
            'scopes'
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
    amendment_number_huawei: Mapped[str | None]

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
            'amendment_remarks',
            'amendment_number_huawei'
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
    clause_action: Mapped[ClauseAction] = mapped_column(
        SqlEnum(ClauseAction), 
        default=ClauseAction.A
    )
    clause_pos: Mapped[ClausePos] = mapped_column(
        SqlEnum(ClausePos), 
        default=ClausePos.M)
    clause_ref: Mapped[str | None]
    clause_type: Mapped[ClauseType] = mapped_column(
        SqlEnum(ClauseType)
    )
    clause_text: Mapped[str | None]
    clause_reviewcomments: Mapped[str | None]
    clause_remarks: Mapped[str | None]
    
    amendment: Mapped['Amendment'] = relationship(
        back_populates='clauses',
        lazy='joined',
        active_history=True,
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

    @property
    def _name(self) -> str:
        return _(self.clause_type.name, True)

    key_info = {
        'data': (
            'clause_id',
            'amendment',
            'amendment_id',
            'clause_action',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_text',
            'clause_reviewcomments',
            'clause_remarks'  
        ),
        'hidden': { 'clause_id', 'amendment_id' },
        'readonly': { 'clause_id', 'amendment' },
        'longtext': { 'clause_text', 'clause_reviewcomments', 'clause_remarks' }
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

    @property
    def _name(self) -> str:
        return super()._name + ': ' + _('Contract', True) + '[' + self.contract._name + '] @ ' + f'{self.termination_date}'

    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_TERMINATION
    }

    key_info = {
        'data': (
            'clause_id',
            'amendment',
            'amendment_id',
            'clause_action',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_text',
            'clause_reviewcomments',
            'clause_remarks',
            'contract_id',
            'contract',
            'termination_date'
        ),
        'hidden': { 'clause_id', 'amendment_id', 'contract_id' },
        'readonly': { 'clause_id', 'amendment', 'contract' },
        'longtext': { 'clause_text', 'clause_reviewcomments', 'clause_remarks' },
        'translate': { }
    }
class ClauseScope(Clause):
    __tablename__ = 'clause_scope'
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
    
    
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

    @property
    def _name(self) -> str:
        nm = super()._name
        if self.clause_action == ClauseAction.A:
            return nm + f' +[{self.new_scope._name}]'
        elif self.clause_action == ClauseAction.R:
            return nm + f' -[{self.old_scope._name}]'
        elif self.clause_action == ClauseAction.U:
            return nm + f' +[{self.new_scope._name}] -[{self.old_scope._name}]'
        else:
            return 'Wrong clause action type'

    key_info = {
        'data': (
            'clause_id',
            'amendment',
            'amendment_id',
            'clause_action',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_text',
            'new_scope_id',
            'new_scope',
            'old_scope_id',
            'old_scope',
            'clause_reviewcomments',
            'clause_remarks'  
        ),
        'hidden': { 'clause_id', 'amendment_id', 'new_scope_id', 'old_scope_id' },
        'readonly': { 'clause_id', 'amendment', 'new_scope', 'old_scope' },
        'longtext': { 'clause_text', 'clause_reviewcomments', 'clause_remarks' },
        'translate': { '_name' }
    }
class ClauseEntity(Clause):
    __tablename__ = 'clause_entity'
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
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
    @property
    def _name(self) -> str:
        nm = super()._name
        if self.clause_action == ClauseAction.A:
            return nm + f' +[{self.new_entity._name}]'
        elif self.clause_action == ClauseAction.R:
            return nm + f' -[{self.old_entity._name}]'
        elif self.clause_action == ClauseAction.U:
            return nm + f' +[{self.new_entity._name}] -[{self.old_entity._name}]'
        else:
            return 'Wrong clause action type'
    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_ENTITY
    }
    key_info = {
        'data': (
            'clause_id',
            'amendment',
            'amendment_id',
            'clause_action',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_text',
            'new_entity_id',
            'new_entity',
            'old_entity_id',
            'old_entity',
            'clause_reviewcomments',
            'clause_remarks'  
        ),
        'hidden': { 'clause_id', 'amendment_id', 'new_entity_id', 'old_entity_id' },
        'readonly': { 'clause_id', 'amendment', 'new_entity', 'old_entity' },
        'longtext': { 'clause_text', 'clause_reviewcomments', 'clause_remarks' },
        'translate': { '_name' }
    }
class ClauseExpiry(Clause):
    __tablename__ = 'clause_expiry'
    clause_id: Mapped[int] = mapped_column(
        Integer,          
        ForeignKey('clause.clause_id'),
        primary_key=True)
    expiry_type: Mapped[ExpiryType] = mapped_column(SqlEnum(ExpiryType))
    expiry_date: Mapped[date | None] = mapped_column(Date)
    applied_to_scope_id: Mapped[int | None] = mapped_column(
        ForeignKey('scope.scope_id')
    )
    linked_to_contract_id: Mapped[int | None] = mapped_column(
        ForeignKey('contract.contract_id')
    )
    linked_to_contract: Mapped['Contract'] = relationship(
        lazy = 'selectin'
    )

    applied_to_scope: Mapped['Scope'] = relationship(
        lazy = 'selectin'
    )

    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_EXPIRY
    }

    @property
    def _name(self) -> str:
        nm = f'{super()._name}: '
        nm += _(self.expiry_type.value, True) + ': '
        if self.expiry_type in {ExpiryType.FD, ExpiryType.LL}:
            return nm + f'{self.expiry_date}'
        else:
            return nm + f'⇄{self.linked_to_contract._name}'

    key_info = {
        'data': (
            'clause_id',
            'amendment',
            'amendment_id',
            'clause_action',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_text',
            'applied_to_scope_id',
            'expiry_type',
            'expiry_date',
            'linked_to_contract_id',
            'linked_to_contract',
            'applied_to_scope',
            'clause_reviewcomments',
            'clause_remarks'  
        ),
        'hidden': { 'clause_id', 'amendment_id', 'applied_to_scope_id', 'linked_to_contract_id' },
        'readonly': { 'clause_id', 'amendment', 'applied_to_scope', 'linked_to_contract' },
        'longtext': { 'clause_text', 'clause_reviewcomments', 'clause_remarks' }
    }
class ClauseCustomerList(Clause):
    __tablename__ = 'clause_customer_list'
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
    @property
    def _name(self) -> str:
        nm = super()._name
        if self.clause_action == ClauseAction.A:
            return nm + f' +[{self.new_customer._name}]'
        elif self.clause_action == ClauseAction.R:
            return nm + f' -[{self.old_customer._name}]'
        elif self.clause_action == ClauseAction.U:
            return nm + f' +[{self.new_customer._name}] -[{self.old_customer._name}]'
        else:
            return 'Wrong clause action type'
    __mapper_args__ = {
        'polymorphic_identity': ClauseType.CLAUSE_CUSTOMER_LIST
    }  
    key_info = {
        'data': (
            'clause_id',
            'amendment',
            'amendment_id',
            'clause_action',
            'clause_type',
            'clause_pos',
            'clause_ref',
            'clause_text',
            'effective_date',
            'new_customer_id',
            'new_customer',
            'old_customer_id',
            'old_customer',
            'clause_reviewcomments',
            'clause_remarks'  
        ),
        'hidden': { 'clause_id', 'amendment_id', 'new_customer_id', 'old_customer_id' },
        'readonly': { 'clause_id', 'amendment', 'new_customer', 'old_customer' },
        'longtext': { 'clause_text', 'clause_reviewcomments', 'clause_remarks' },
        'translate': { '_name' }
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
        'readonly': { 'entitygroup_id' },
        'translate': { 'entitygroup_name' }
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
        'hidden': { 'entity_id', 'entitygroup_id' },
        'readonly': { 'entity_id', 'entitygroup' },
        'translate': { '_name', 'entity_name' }
    }
class Scope(Base):
    __tablename__ = 'scope'
    scope_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope_name: Mapped[str]
    
    _name = synonym('scope_name')
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

    key_info = {
        'data': ( 'scope_id', 'scope_name', 'parent_scopes', 'child_scopes' ),
        'hidden': { 'scope_id' },
        'readonly': { 'scope_id', 'parent_scopes', 'child_scopes' },
        'translate': { '_name', 'scope_name' }
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
        'data': (
            'parent_scope_id',
            'parent_scope',
            'child_scope_id',
            'child_scope'
        ),
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

    key_info = {
        'data': (
            'parent_contract_id',
            'parent_contract',
            'child_contract_id',
            'child_contract'
        ),
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

    key_info = {
        'data': (
            'parent_contract_id',
            'parent_contract',
            'child_contract_id',
            'child_contract'
        ),
        'hidden': { 'parent_contract_id', 'child_contract_id' },
        'readonly': { 'parent_contract', 'child_contract' }
    }  

Contract.scopes.fget.info = {'type': 'list'}
Contract.entities.fget.info = {'type': 'list'}
