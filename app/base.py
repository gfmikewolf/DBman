# app/base_mixin.py
from typing import List, Type, Set
from sqlalchemy import select, Select
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.sql.expression import ColumnClause
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    # 当前用户可访问的表与数据模型的映射
    map_table_Model = {}

    # 查询所有数据，排除特定信息的列属性，添加关联模型的属性
    @classmethod
    def query_all(cls, exclude: List[str]=['hidden'], with_ref_attrs: bool=True) -> Select:
        query_columns = []
        for ex_info in exclude:
            exclude_columns = cls.attr_info.get(ex_info, [])
            for attr in cls.__mapper__.column_attrs:
                if attr not in exclude_columns:
                    query_columns.append(attr)
        join_models = []
        if with_ref_attrs:
            ref_map = cls.attr_info.get('ref_map', {})
            for join_model, attr_orderby_dict in ref_map.items():
                for ref_name_attr in attr_orderby_dict.keys():
                    if ref_name_attr is not None and join_model is not None:
                        query_columns.append(ref_name_attr)
                        join_models.append(join_model)
        query = select(*query_columns)
        if join_models:
            query = query.select_from(cls)
            for model in join_models:
                query = query.join(model)
        return query
    
    # 获取关联属性的选项
    @classmethod
    def query_all_ref_attrs(cls, new_order_by: dict[ColumnProperty, List[ColumnProperty | ColumnClause]]={}) -> dict[ColumnProperty, Select]:
        queries = {}
        ref_map = cls.attr_info.get('ref_map', {})
        for model, attr_orderby_dict in ref_map.items():
            query_columns = []
            order_by_columns = []
            for ref_name_attr, order_by in attr_orderby_dict.items():
                if ref_name_attr is not None and model is not None:
                    query_columns.append(ref_name_attr)
                    replace_order_by = []
                    if new_order_by:
                        replace_order_by = new_order_by.get(ref_name_attr, [])
                    if replace_order_by:
                        order_by_columns.extend(replace_order_by)
                    elif order_by:
                        order_by_columns.extend(order_by)
                    query = select(*query_columns)
                    if order_by_columns:
                        query = query.order_by(*order_by_columns)
                    queries[ref_name_attr] = query
        return queries
