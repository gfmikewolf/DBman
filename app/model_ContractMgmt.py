# app/model_ContractMgmt.py
from typing import List, Type, Set
from sqlalchemy import ForeignKey, create_engine, select, inspect, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, synonym
from sqlalchemy.orm import Session
from datetime import date

class Base(DeclarativeBase):
    """ 返回实例的字典，data_type默认是'raw'。
    data_type='raw'时返回的是所有映射列的列名:列值
    data_type='rel_name'时返回的值只有外键列不同，逻辑如下：
        外键定义中info信息同时存在关系名rel_name和引用类属性名fk_attr_name时：
            用{关系名：引用类属性值}替换raw生成的数据中{列名:列值}，
            具体来说expense_type_id:1会被替换成expense_type:日常消费
    """
    def data_dict(self, data_style='raw') -> dict | None:
        data_dict = {}
        mapper = self.__mapper__
        if data_style == 'raw':
            data_dict = {key: getattr(self, key) for key in mapper.column_attrs.keys()}
        elif data_style == 'rel_name':
            for col in mapper.columns:
                data_key = mapper.get_property_by_column(col).key
                data_value = getattr(self, data_key)
                if col.foreign_keys:
                    rel_name = col.info.get('rel_name')
                    fk_attr_name = col.info.get('fk_attr_name')
                    if not fk_attr_name:
                        fk_attr_name = 'name'
                    if rel_name and fk_attr_name:
                        fk_rel = getattr(self, rel_name)
                        if fk_rel:
                            fk_value = getattr(fk_rel, fk_attr_name)
                            if fk_value:
                                data_key = rel_name
                                data_value = fk_value
                            else:
                                print('foreign key is not bound with a valid reference table or value')
                                return None
                        else:
                            print('relationship is not found by rel_name of the foreign key')
                            return None
                data_dict[data_key] = data_value
        return data_dict

    # 获取类的属性名列表, data_style='rel_name'时返回的值替换外键为关系名(通常为引用类的表名)
    @classmethod
    def get_prop_info(cls, data_style='raw', nullable=True, include_info: Set[str] = set(), exclude_info: Set[str] = set()) -> List[dict] | None:
        # Validate include_info and exclude_info are sets
        if not isinstance(include_info, set) or not isinstance(exclude_info, set):
            raise ValueError("include_info and exclude_info must be sets")

        # Validate that include_info and exclude_info contain only valid options
        valid_options = {'readonly', 'hidden', 'attachment'}
        if not include_info.issubset(valid_options) or not exclude_info.issubset(valid_options):
            raise ValueError(f"include_info and exclude_info must contain only valid options: {valid_options}")

        mapper = cls.__mapper__
        prop_info = []
        for col in mapper.columns:
            pi = {}
            if not nullable and col.nullable:
                continue
            if include_info:
                if not any([col.info.get(info_key) for info_key in include_info]):
                    continue
            if exclude_info:
                if any([col.info.get(info_key) for info_key in exclude_info]):
                    continue
            rel_name = ''
            pi_key = mapper.get_property_by_column(col).key
            if col.foreign_keys:
                rel_name = col.info.get('rel_name')
                if rel_name and data_style == 'rel_name':
                    pi_key = rel_name
            pi['key'] = pi_key
            pi['default'] = str(col.default.arg) if col.default else ''
            pi['is_foreignkey'] = True if col.foreign_keys else False
            pi['is_required'] = not col.nullable
            pi['rel_name'] = rel_name
            pi['is_date'] = col.key.endswith('date')
            pi['is_json'] = col.key.endswith('json')
            prop_info.append(pi)
        return prop_info

class ForeignKeyMixin:
    # 获取外键属性的选项字典，用于前端显示外键的意义
    @classmethod
    def get_options_fk(cls, session: Session, order_by_attr=None, order_by_desc=False) -> dict:
        options = {}
        mapper = cls.__mapper__
        for col in mapper.columns:
            if not col.foreign_keys: continue
            rel_name = col.info.get('rel_name')
            if not rel_name: continue
            rel = getattr(cls, rel_name)
            rel_cls = rel.mapper.class_
            if not rel_cls: continue
            # Check if the related class has 'id' and 'name' attributes
            if hasattr(rel_cls, 'id') and hasattr(rel_cls, 'name'):
                stmt = (
                    select(rel_cls.id, rel_cls.name)
                    # Add order_by if needed
                )
                if order_by_attr:
                    rel_order_by_attr = getattr(rel_cls, order_by_attr[rel_name])
                    if order_by_desc:
                        stmt = stmt.order_by(rel_order_by_attr.desc())
                    else:
                        stmt = stmt.order_by(rel_order_by_attr)
                results = session.execute(stmt).all()
                options[rel_name] = {row.id: row.name for row in results}
            else:
                print(f'no id or name attribute in {rel_cls}')
        return options

    # 获取外键属性名列表
    @classmethod
    def get_properties_fk(cls) -> Type[str]:
        mapper = cls.__mapper__
        return [mapper.get_property_by_column(col).key for col in mapper.columns if col.foreign_keys]

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

class UserRole(Base):
    __tablename__ = 'user_role'
    user_role_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    user_role_name: Mapped[str]
    
    users: Mapped[List['User']] = relationship(
        back_populates='user_roles', 
        lazy='select',
        secondary='map_user__user_role')

class MAPUserANDUserRole(ForeignKeyMixin, Base):
    __tablename__ = 'map_user__user_role'
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.user_id'),
        primary_key=True,
        info={
            'rel_name': 'user', 
            'fk_attr_name':'user_name'
        }
    )
    user_role_id: Mapped[int] = mapped_column(
        ForeignKey('user_role.user_role_id'),
        primary_key=True,
        info={
            'rel_name': 'user_role', 
            'fk_attr_name':'user_role_name'
        }
    )

class User(ForeignKeyMixin,Base):
    __tablename__ = 'user'
    user_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    user_name: Mapped[str]
    user_password_hash: Mapped[str] = mapped_column(info={'readonly': True})
    user_role_id: Mapped[int] = mapped_column(
        ForeignKey('user_role.user_role_id'),
        info={
            'rel_name': 'user_role', 
            'fk_attr_name':'user_role_name'
        }
    )
    id = synonym('user_id')
    name = synonym('user_name')

    user_roles: Mapped[List['UserRole']] = relationship(
        back_populates='users', 
        lazy='select',
        secondary='map_user__user_role')
    
    @classmethod
    def get_options_fk(cls, session: Session):
        order_by_attr = {
            "user_role": "user_role_name",
        }
        return super().get_options_fk(session, order_by_attr=order_by_attr)
    
class ClauseType(Base):
    __tablename__ = 'clause_type'
    clause_type_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    clause_type_name: Mapped[str]
    clauses: Mapped['Clause'] = relationship(
        back_populates='clause_type',
        lazy = 'select'
    )
    id = synonym('clause_type_id')
    name = synonym('clause_type_name')

class ClausePos(Base):
    __tablename__ = 'clause_pos'
    clause_pos_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    clause_pos_name: Mapped[str] = mapped_column(default='', nullable=False)
    clauses: Mapped['Clause'] = relationship(
        back_populates='clause_pos',
        lazy = 'select'
    )
    id = synonym('clause_pos_id')
    name = synonym('clause_pos_name')

class Clause(ForeignKeyMixin, Base):
    __tablename__ = 'clause'
    clause_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    clause_type_id: Mapped[int] = mapped_column(
        ForeignKey('clause_type.clause_type_id'),
        info={
            'rel_name': 'clause_type', 
            'fk_attr_name':'clause_type_name'
        }
    )
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

DBModel = {
    'contract': Contract,
    'amendment': Amendment,
    'clause': Clause,
    'clause_type': ClauseType,
    'clause_pos': ClausePos,
    'user': User,
    'user_role': UserRole,

}
