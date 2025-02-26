# app/base_mixin.py
from typing import List, Type, Set
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session

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
            pi['is_extension'] = col.info.get('extension', False)
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

class JSONMixin:
    pass
