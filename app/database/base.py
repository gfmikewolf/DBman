# app/database/base.py
import logging
import json
from math import e
from typing import Any
from datetime import date
from enum import Enum
from sqlalchemy import (
    Result, select, Select
)
from sqlalchemy.orm import (
    DeclarativeBase,
    ColumnProperty
)
from sqlalchemy.sql.expression import ColumnClause
from copy import deepcopy
from app.utils.type_tools import convert_string_by_attr_type
from .jsonbase import JsonBase

class Base(DeclarativeBase):
    # 当前用户可访问的表与数据模型的映射
    map_table_Model: dict[str, 'Base'] = {}
    """
    map_table_Model: dict[str, Base]
        当前用户可访问的表与数据模型的映射。
    """

    attr_info_keys: dict[str, set[str]] = {
        'hidden': set(),
        'readonly': set(),
        'pk': set(),
        'date': set(),
        'required': set(),
        'json': set(),
        'ref': set()
    }
    """
    attr_info_keys: dict[str, set[str]]
        - hidden: set[str]
            隐藏的列属性键集合。
        - readonly: set[str]
            只读的列属性键集合。
        - pk: set[str]
            主键列属性键集合。
        - date: set[str]
            日期列属性键集合。
        - required: set[str]
            必需的列属性键集合。
        - json: set[str]
            JSON 列属性键集合。
        - ref: set[str]
            关联模型的列属性键集合。
    """
    
    attr_info: dict[str, Any] = {
        'hidden': set(),
        'readonly': set(),
        'json_classes': dict(),
        'pk': set(),
        'date': set(),
        'ref_map': dict(),
        'required': set()
    }
    """
    attr_info: dict[str, Any]
    - hidden: set[cls.attrs: ColumnProperty]
    - readonly: set[cls.attrs: ColumnProperty]
    - pk: set[cls.attrs: ColumnProperty]
    - date: set[cls.attrs: ColumnProperty]
    - required: set[cls.attrs: ColumnProperty]
    - json_classes: dict [
        - cls.attr: ColumnProperty, 
        - json_classes: dict[
            - 'type': set['polymorphic', 'onetoone']
            - 'json_class': jsonBase = onetoone class
            - 'identity_on': attr.key: str for polymorphic classification
            - 'identity_map': dict[identity_on_attr.value:Any, json_class: Any]
    - ref_map: dict[
        - ref_model: Base, 
        - dict[
            - 'ref_name_attr': ref_name_attr: ColumnProperty, 
            - 'order_by': order_by_params: list[ColumnProperty | ColumnClause] ] ]
    """

    @classmethod
    def get_attr_keys(cls, include_info: tuple[str, ...]) -> set[str]:
        """
        获取包含指定信息的列属性键集合。

        - 参数:
        include_info (tuple[str, ...]): 包含的信息集合。

        - 返回:
        set[str]: 包含指定信息的列属性键集合。
        """
        attr_keys = set()
        for key in include_info:
            if key not in cls.attr_info_keys:
                raise AttributeError(f'Wrong include_info {key} in {cls}')
            info_keys = cls.attr_info_keys.get(key, set())
            if not info_keys:
                if key == 'json':
                    json_attrs = cls.attr_info.get('json_classes', {}).keys()
                    info_keys.update({json_attr.name for json_attr in json_attrs})
                if key == 'ref':
                    ref_attrs = cls.attr_info.get('ref_map', {}).keys()
                    info_keys.update({ref_attr.name for ref_attr in ref_attrs})
                else:
                    info_keys.update({attr.name for attr in cls.attr_info.get(key, set())})
                cls.attr_info_keys[key].update(info_keys)
            attr_keys.update(info_keys)
        return attr_keys

    def __init__(self, form_data: dict[str, str] | None = None):
        """
        初始化模型实例。如果提供了 form_data，则使用表单数据初始化实例。

        参数:
        form_data (dict[str, str], 可选): 表单数据的字典，其中键是表单字段名，值是表单字段的值。
        """
        super().__init__()
        if form_data is not None:
            for key, value in form_data.items():
                setattr(self, key, value)
    
    def __setattr__(self, key: str, value: Any) -> None:
        """

        """
        readonly_keys = self.get_attr_keys(('readonly',))
        date_keys = self.get_attr_keys(('date',))
        json_keys = self.get_attr_keys(('json',))
        
        if key in readonly_keys or key in json_keys:
            return
        if key in date_keys:
            if isinstance(value, str):
                value = date.fromisoformat(value)
        elif key in json_keys and isinstance(value, str):
            value = JsonBase.loads(value)
        else:
            super().__setattr__(key, value)

    @classmethod
    def get_columns(cls, attr_info_keys: tuple[str,...]) -> list[ColumnProperty]:
        info_keys = list(attr_info_keys)
        attrs = []
        for key in info_keys:
            attrs.extend(cls.attr_info.get(key, []))
        return attrs

    @classmethod
    def query_all(cls, exclude: tuple[str, ...]=('hidden',), with_ref_attrs: bool=True) -> Select:
        """
        查询所有数据，排除特定信息的列属性，添加关联模型的属性。

        参数:
        exclude (tuple[str, ...]): 需要排除的列属性，默认为 ('hidden',)。
        with_ref_attrs (bool): 是否添加关联模型的属性，默认为 True。

        返回:
        Select: 一个 SQLAlchemy Select 对象，用于查询数据。
        """
        pk_columns = cls.attr_info.get('pk', [])
        if not pk_columns:
            raise AttributeError(f'Primary key not defined in {cls} attr_info')
        query_columns = []
        exclude_columns = cls.get_columns(exclude)
        exclude_columns.extend(pk_columns)
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
        query = select(*pk_columns,*query_columns)
        if join_models:
            query = query.select_from(cls)
            for model in join_models:
                query = query.join(model)
        return query
    
    @classmethod
    def query_all_ref_attrs(cls, new_order_by: dict[ColumnProperty, list[ColumnProperty | ColumnClause]] = {}) -> dict[ColumnProperty, Select]:
        """
        获取所有关联属性的查询选项。

        该方法生成一个包含所有关联属性查询的字典，每个键是关联属性，
        值是一个 SQLAlchemy Select 对象，用于查询该属性的值。

        参数:
        new_order_by (dict[ColumnProperty, list[ColumnProperty | ColumnClause]]): 
            一个可选的字典，用于指定新的排序规则。字典的键是关联属性，
            值是一个包含排序列的列表。如果未提供，则使用默认的排序规则。

        返回:
        dict[ColumnProperty, Select]: 一个字典，其中键是关联属性，值是对应的查询对象。
        """
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

    @classmethod
    def split_result(cls, result: Result, exclude_info: tuple[str, ...]=('hidden',)) -> tuple[list[str], list[str], list[str], list[list[Any]]]:
        """
        从查询结果中分离出主键列和其他列的数据。本函数需要主键在最左侧，主要用于cls.query_all()的结果，否则会出现错误。

        参数:
        result (Result): 查询结果对象。
        exclude (tuple[str, ...]): 需要排除的列属性，默认为 ('hidden',)。

        返回:
        tuple[list[str], list[list[Any]]]: 包含主键列和其他列数据的元组。
        """
        pk_attrs = cls.attr_info.get('pk', [])
        if not pk_attrs:
            raise AttributeError('Primary key not defined in {cls} attr_info')

        exclude_columns = cls.get_columns(exclude_info)
       
        pk_len = len(pk_attrs)
        hidden_pk_len = pk_len
        for pk_attr in pk_attrs:
            if pk_attr not in exclude_columns:
                hidden_pk_len -= 1
        pks = []
        data = []
        theads = list(result.keys())[hidden_pk_len:]
        for row in result:
            pks.append(','.join([str(row[i]) for i in range(pk_len)]))
            data.append(row[pk_len:])
        json_cols = [key.name for key in cls.attr_info.get('json_classes', {}).keys()]
        return pks, theads, json_cols, data
    
    @classmethod
    def retrieve_tuple_pks(cls, pks: str) -> tuple[Any, ...]:
        """
        从字符串中解析出主键元组，并将其转换为相应的类型。

        参数:
        pks (str): 包含主键值的字符串。

        返回:
        tuple[Any, ...]: 包含主键值的元组。
        """
        pk_attrs = cls.attr_info.get('pk', [])
        if not pk_attrs:
            raise AttributeError(f'Primary key not defined in {cls} attr_info')
        pk_values = pks.split(',')
        if len(pk_values) != len(pk_attrs):
            raise ValueError(f'Primary key values not fully set: {pk_values}')
        
        # 将字符串格式的主键值转换为相应的类型
        converted_pk_values = []
        for pk_attr, pk_value in zip(pk_attrs, pk_values):
            converted_value = convert_string_by_attr_type(pk_attr, pk_value)
            if converted_value is None:
                raise ValueError(f'Failed to convert primary key value: {pk_value}')
            converted_pk_values.append(converted_value)
        
        return tuple(converted_pk_values)
    
    @classmethod
    def form_to_dict(cls, form_data: dict[str, str]) -> dict[str, Any]:
        """
        将表单数据转换为字典，并将其转换为相应的类型。

        参数:
        form_data (dict[str, str]): 表单数据的字典，其中键是表单字段名，值是表单字段的值。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。

        异常:
        AttributeError: 如果表单数据缺少必需的键，或者在模型中找不到相应的属性。
        ValueError: 如果表单数据的值无法转换为预期的类型。
        """
        mapper = cls.__mapper__
        data_attrs = mapper.column_attrs
        required = cls.attr_info.get('required', [])
        readonly = cls.attr_info.get('readonly', [])
        json_classes = cls.attr_info.get('json_classes', {})
        data_dict = {}
        for data_attr in data_attrs:
            if data_attr in required and data_attr.name not in form_data:
                raise AttributeError(f'Required key {data_attr} not found in form data')
            if data_attr in readonly:
                converted_value = None
            if data_attr in json_classes.keys():
                classes_info = json_classes[data_attr]
                if classes_info.get('identity_on') is None:
                    raise AttributeError(f'Identity attribute not found in json_classes')
                identity_on = getattr(cls, classes_info['identity_on'], None)
                if identity_on is None:
                    raise AttributeError(f'Identity attribute {classes_info["identity_on"]} not found in Model {cls}')
                identity_attr = classes_info.get('identity_attr', None)
                if identity_attr is None:
                    raise AttributeError(f'Identity attribute not found in json_classes')
                
                identity_value = getattr(identity_on, identity_attr, None)
                if identity_value is None:
                    raise AttributeError(f'Identity attribute {identity_attr} not found in Model {identity_on}')
                classes_map = classes_info[identity_on].get('json_classes', {})
                if not classes_map:
                    raise AttributeError(f'Json classes map not found in {classes_info.identity_on}')
                json_class = classes_map.get(identity_value, None)
                if json_class is None:
                    raise AttributeError(f'Json class not found in {classes_map} with key {identity_value}')
                if not issubclass(json_class, JsonBase):
                    raise AttributeError(f'Json class {json_class} is not subclass of JsonBase')
                converted_value = json.loads(form_data[key], object_hook=json_classes[key].object_hook)
            else:
                converted_value = convert_string_by_attr_type(attr, form_data[key])
            if converted_value is None:
                raise ValueError(f'Value cannot be converted as expected {key}:{form_data[key]}')
            data_dict[key] = converted_value
        return data_dict

    def update_from_form(self, form_data: dict[str, str]) -> bool:
        """
        使用表单数据更新模型实例。

        参数:
        form_data (dict[str, str]): 表单数据的字典，其中键是表单字段名，值是表单字段的值。

        返回:
        bool: 如果更新成功返回 True，否则返回 False。

        异常:
        AttributeError: 如果表单数据缺少必需的键，或者在模型中找不到相应的属性。
        ValueError: 如果表单数据的值无法转换为预期的类型。
        """
        original_data = deepcopy(self.__dict__)  # 深拷贝原始数据
        
        try:
            dict_data = self.form_to_dict(form_data)
            for key, value in dict_data.items():
                setattr(self, key, value)
            return True
        except Exception as e:                
            # 恢复原始数据，排除以双下划线开头的内置属性
            self.__dict__.update({k: v for k, v in original_data.items() if not k.startswith('__')})
            logging.error(f"Error in updating {self}. Error: {e}")
            return False

