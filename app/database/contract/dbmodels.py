# app/database/contract/contract.py
from typing import List
from sqlalchemy import ForeignKey, Date,Integer, String, select, Select
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from datetime import date
from app.database.base import Base

class Contract(Base):
    __tablename__ = 'contract'
    contract_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_name: Mapped[str] = mapped_column(String)
    contract_fullname: Mapped[str | None] = mapped_column(String)
    contract_effectivedate: Mapped[date] = mapped_column(Date)
    contract_expirydate: Mapped[date] = mapped_column(Date)
    contract_scope: Mapped[str] = mapped_column()
    contract_entities: Mapped[str | None] = mapped_column(String)
    contract_remarks: Mapped[str | None] = mapped_column(String)
    contract_number_huawei: Mapped[str | None] = mapped_column(String)
    contract_number_customer: Mapped[str | None] = mapped_column(String)
    
    pks = synonym('contract_id')
    name = synonym('contract_name')
    
    amendments: Mapped[List['Amendment']] = relationship(
        back_populates='contract', 
        lazy='select', 
    )

    @classmethod
    def select_all(cls) -> Select:
        if cls.db_session is None:
            raise ValueError("db_session is not set in the Base class")
        with cls.db_session() as sess:
            return sess.execute(select(cls)).scalars().all()

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
        'required': [contract_name],
        'date': [contract_effectivedate, contract_expirydate]
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
    amendment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
            Contract: {
                'ref_name_attr': Contract.contract_name,
                'order_by': [Contract.contract_name]
            }
        },
        'date': [amendment_signdate, amendment_effectivedate]
    }

class Clause(Base):
    __tablename__ = 'clause'
    clause_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clause_type: Mapped[ClauseType] = mapped_column(Integer, ForeignKey('clause_type.clause_type_id'))
    clause_ref: Mapped[str | None]
    clause_text: Mapped[str | None]
    amendment_id: Mapped[int] = mapped_column(Integer, ForeignKey('amendment.amendment_id'))
    clause_pos: Mapped[ClausePos] = mapped_column(Integer, ForeignKey('clause_pos.clause_pos_id'))
    clause_reviewcomments: Mapped[str | None]
    clause_remarks: Mapped[str | None]
    clause_effectivedate: Mapped[date | None] = mapped_column(Date)
    clause_expirydate: Mapped[date | None] = mapped_column(Date)
    clause_json: Mapped[JsonBase] = mapped_column(JsonBaseType)
    
    amendment: Mapped['Amendment'] = relationship(
        back_populates='clauses',
        lazy='selectin'
    )

    attr_info = {
        'pk': [clause_id],
        'hidden': [clause_id, clause_type, clause_pos],
        'readonly': [clause_id],
        'required': [clause_type, amendment_id, clause_pos, clause_json],
        'json_classes': {
            clause_json: {
                'type': 'polymorphic',
                'identity_on': 'clause_type',
                'identity_map': {
                    ClauseType.EXPIRY : ClauseExpiry,
                    ClauseType.ENTITY : ClauseEntity,
                    ClauseType.SCOPE : ClauseScope
                }
            }
        },
        'ref_map': {
            Amendment : {
                'ref_name_attr': Amendment.amendment_name,
                'order_by': [Amendment.amendment_name]
            }
        },
        'date': [clause_effectivedate, clause_expirydate]
    }

class Entitygroup(Base):
    __tablename__ = 'entitygroup'
    entitygroup_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entitygroup_name: Mapped[str]

    pks = synonym('entitygroup_id')

    entities: Mapped[List['Entity']] = relationship(
        back_populates='entitygroup',
        lazy='select'
    )

class Entity(Base):
    __tablename__ = 'entity'
    entity_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String)
    entity_fullname: Mapped[str | None]
    entitygroup_id: Mapped[int] = mapped_column(ForeignKey('entitygroup.entitygroup_id'))
    
    pks = synonym('entity_id')

    entitygroup: Mapped['Entitygroup'] = relationship(
        back_populates='entities',
        lazy='selectin'
    )

    @classmethod
    def select_all(cls, with_ref_name=True) -> Select:
        return select(
            Entity.entity_id, 
            Entity.entity_name, 
            Entity.entity_fullname,
            Entitygroup.entitygroup_name).join_from(Entity, Entitygroup)
    

