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
    def get_properties(cls, data_style='raw', include_info: Set[str] = set(), exclude_info: Set[str] = set()) -> Type[str] | None:
        # Validate include_info and exclude_info are sets
        if not isinstance(include_info, set) or not isinstance(exclude_info, set):
            raise ValueError("include_info and exclude_info must be sets")

        # Validate that include_info and exclude_info contain only valid options
        valid_options = {'readonly', 'hidden', 'attachment'}
        if not include_info.issubset(valid_options) or not exclude_info.issubset(valid_options):
            raise ValueError(f"include_info and exclude_info must contain only valid options: {valid_options}")

        mapper = cls.__mapper__
        props = []
        for col in mapper.columns:
            if include_info:
                if not any([col.info.get(info_key) for info_key in include_info]):
                    continue
            if exclude_info:
                if any([col.info.get(info_key) for info_key in exclude_info]):
                    continue
            prop = mapper.get_property_by_column(col).key
            if col.foreign_keys and data_style == 'rel_name':
                rel_name = col.info.get('rel_name')
                if rel_name:
                    prop = rel_name
            props.append(prop)
        return props

class ForeignKeyMixin:
    # 获取外键属性的选项字典，用于前端显示外键的意义
    @classmethod
    def get_options_fk(cls, session: Session, order_by_attr=None, order_by_desc=False) -> dict:
        options = {}
        mapper = cls.__mapper__
        for relationship in mapper.relationships:
            rel_cls = relationship.mapper.class_

            # Check if the related class has 'id' and 'name' attributes
            if hasattr(rel_cls, 'id') and hasattr(rel_cls, 'name'):
                stmt = (
                    select(rel_cls.id, rel_cls.name)
                    # Add order_by if needed
                )
                if order_by_attr:
                    rel_order_by_attr = getattr(rel_cls, order_by_attr[relationship.key])
                    if order_by_desc:
                        stmt = stmt.order_by(rel_order_by_attr.desc())
                    else:
                        stmt = stmt.order_by(rel_order_by_attr)
                results = session.execute(stmt).all()
                options[relationship.key] = {row.id: row.name for row in results}
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
    amendment_remarks: Mapped[str]
    contract_id: Mapped[int] = mapped_column(ForeignKey('contract.contract_id'), info={'rel_name': 'contract', 'fk_attr_name':'contract_name'})
    
    id = synonym('amendment_id')
    name = synonym('amendment_name')
    
    contract: Mapped['Contract'] = relationship(back_populates='amendments', lazy='selectin')

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

DBModel = {
    'contract': Contract,
    'amendment': Amendment
}
