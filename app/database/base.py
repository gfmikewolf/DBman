# app/database/base.py
"""
Base 模块包含了 Base 类，该类是所有数据模型类的基类。
"""
from calendar import c
import logging
import json
from pydoc import visiblename
from sqlite3 import DatabaseError
from typing import Any, Iterable
from enum import Enum
from datetime import date
from xml.etree.ElementInclude import include
from sqlalchemy import (
    ColumnExpressionArgument, ForeignKey, ForeignKeyConstraint, Result, select, Select
)

from sqlalchemy.orm import (
    DeclarativeBase,
    ColumnProperty,
    scoped_session
)
from sqlalchemy.sql.expression import ColumnClause
from copy import deepcopy
from app.database.datajson import DataJson  # Adjust the import path as necessary


class Base(DeclarativeBase):
    # 当前用户可访问的表与数据模型的映射
    model_map: dict[str, type['Base']] = {}
    """
    map_table_Model: dict[str, Base]
        当前用户可访问的表与数据模型的映射。
    """

    db_session: scoped_session | None = None
    """
    db_session: scoped_session

    SQLAlchemy 会话对象，用于与数据库进行交互。
    """

    attr_info_keys: dict[str, set[str]] = {}
    
    attr_info: dict[str, Any] = {
        'required': set(),
        'hidden': set(),
        'readonly': set()
    }

    _data_dict : dict = {}

    def __init__(self, data: str | dict | None = None, **kwargs: Any) -> None:
        """
        初始化模型实例。如果提供了 form_data，则使用表单数据初始化实例。

        参数:
        form_data (dict[str, str], 可选): 表单数据的字典，其中键是表单字段名，值是表单字段的值。
        """
        super().__init__()
        args_dict = Base._args_to_dict(data, **kwargs)
        if not self.validate_attr_dict(args_dict):
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {self}')
        mod_attrs = self.get_attrs('modifiable')
        for attr in mod_attrs:
            attr = args_dict[attr.name]
            self._data_dict[attr.name] = attr
    
    @staticmethod
    def _args_to_dict(data: str | dict | None = None, **kwargs: Any) -> dict[str, Any]:
        """
        将参数转换为数据字典。

        参数:
        data (str | dict | None): JSON 字符串或字典。
        kwargs (Any): 其他关键字参数。

        返回:
        dict[str, Any]: 数据字典。
        """
        if data is None:
            data_dict = {}
        elif isinstance(data, str):
            data_dict = json.loads(data)
        elif isinstance(data, dict):
            if kwargs and data:
                data_dict = deepcopy(data) # 防止load函数修改用户data原始数据
            else:
                data_dict = data
        else:
            raise ValueError(f'Invalid data type for arguments (data={data}, kwargs={kwargs})')
        if kwargs:
            data_dict.update(kwargs)
        return data_dict
    
    @classmethod
    def get_attrs(cls, *args: str) -> set[ColumnProperty]:
        """
        获取包含指定信息的列属性集合。
        
        参数:
        include_info (tuple[str, ...]): 包含的信息集合。
        
        返回:
        set[ColumnProperty]: 包含指定信息的列属性集合。
        """
        attrs = {}
        for info in args:
            if info in cls.attr_info:
                attrs.update(cls.attr_info[info])
            elif info == 'data':
                cached = set().update(cls.__mapper__.column_attrs)
                cls.attr_info[info] = cached
                attrs.update(cached) # type: ignore
            elif info == 'pk':
                cached = set()
                for attr in cls.__mapper__.column_attrs:
                    if attr in cls.__mapper__.primary_key:
                        cached.add(attr)
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info == 'modifiable':
                cached = cls.get_attrs('data') - cls.get_attrs('readonly')
                cls.attr_info[info] = cached
                attrs.update(cached) # type: ignore
            elif info == 'visible':
                cached = cls.get_attrs('data') - cls.get_attrs('hidden')
                cls.attr_info[info] = cached
                attrs.update(cached) # type: ignore
            elif info in ('date', 'json', 'int', 'float', 'bool', 'set', 'list', 'dict'):
                cached = set()
                for attr in cls.__mapper__.column_attrs:
                    if isinstance(attr.type.python_type, eval(info)):
                        cached.add(attr)
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info in ('DataJson', 'Enum'):
                cached = set()
                for attr in cls.__mapper__.column_attrs:
                    if issubclass(attr.type.python_type, eval(info)):
                        cached.add(attr)
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info == 'ref_name':
                cached = set()
                for col in cls.__mapper__.columns:
                    fks = col.foreignkeys
                    if col.type.python_type == int:
                        for fk in fks:
                            table = fk.column.table
                            if table is not None:
                                ref_name_attr = getattr(table, 'name', None)
                                if ref_name_attr is not None:
                                    cached.add(ref_name_attr)
                cls.attr_info[info] = cached
                attrs.update(cached)    
            else:
                raise AttributeError(f'Invalid info {info} in {cls}')
        return attrs # type: ignore
    
    @classmethod
    def get_attr_keys(cls, *args: str) -> set[str]:
        attr_keys = set()
        for arg in args:
            keys = cls.attr_info_keys.get(arg, None)
            if not keys:
                attrs = cls.get_attrs(arg)
                keys = {attr.name for attr in attrs}
                cls.attr_info_keys[arg] = keys
            attr_keys.update(keys) # type: ignore
        return attr_keys # type:ignore
    
    @classmethod
    def validate_attr_dict(cls, data : dict[str, Any]) -> bool:
        """
        验证数据字典中的数据是否符合模型的属性要求。

        参数:
        data (dict[str, Any]): 数据字典。

        返回:
        bool: 如果数据字典中的数据符合模型的属性要求，则返回 True，否则返回 False。
        """
        required_keys = cls.get_attr_keys('required')
        missing_keys = required_keys - data.keys()
        if missing_keys:
            return False
        return True

    @classmethod
    def _dict_to_data_dict(cls, args_dict: dict[str, Any]) -> dict[str, Any]:
        """
        将字典中对应attr_info里'data'类型的数据按_tablename的类属性进行数据类型转换。
        - 如果数据缺失'required'属性，抛出属性异常。
        - 忽略'readonly'键的数据

        参数:
        args_dict (dict[str, Any]): 原始数据。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        if not cls.validate_attr_dict(args_dict):
            raise AttributeError('Invalid data: {args_dict} to match {cls}')
            
        data_attrs = cls.get_attrs('modifiable')

        data_dict = {}
        data_dict['__tablename__'] = cls.__tablename__
        
        for data_key in data_attrs:
            value = args_dict.get(data_key.name, None)
            if data_key in args_dict:
                data_dict[data_key.name] = cls.convert_value_by_attr_type(data_key, value)
        return data_dict

    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
        """
        将JSON字符串或字典转换为字典。

        参数:
        data (dict | str | None): JSON字符串或字典。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        args_dict = Base._args_to_dict(data, **kwargs)
        if not cls.validate_attr_dict(args_dict):
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {cls}')

        if not args_dict:
            return args_dict
        else:
            return cls.load_dict(args_dict)
          
    @classmethod
    def load_dict(cls, data: dict) -> dict[str, Any]:   
        """
        将字典中对应attr_info里'data'类型的数据按_tablename的类属性进行数据类型转换。
        - 如果数据缺失'required'属性，抛出属性异常。
        - 忽略'readonly'键的数据

        参数:
        data (dict): 原始数据。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        if cls.__tablename__ is None:
            tablename = data.get('__tablename__', None)
            Model = cls.model_map.get(tablename, None)
            if Model is None:
                raise AttributeError(f'Invalid {tablename} in model_map {cls.model_map}')
        else:
            tablename = cls.__tablename__
            Model = cls
                  
        mod_attrs = Model.get_attrs('modifiable')

        data_dict = {}
        data_dict['__tablename__'] = tablename
        
        for mod_attr in mod_attrs:
            value = data.get(mod_attr.name, None)
            if mod_attr in data:
                data_dict[mod_attr.name] = Model.convert_value_by_attr_type(mod_attr, value)
        return data_dict

    @classmethod
    def convert_value_by_attr_type(cls, attr: ColumnProperty, value: Any) -> Any:
        """
        根据属性类型转换值。如果value不在data_keys中，不进行转换。

        参数:
        attr (ColumnProperty): 属性键。
        value (Any): 属性值。

        返回:
        Any: 转换后的属性值。
        """    
        data_keys = cls.attr_info.get('data', set())
        converted_value = value
        if attr in data_keys:
            attr_type = attr.type.python_type
            if attr_type == type(value):
                return value
            if attr_type == date and isinstance(value, str):
                converted_value = date.fromisoformat(value)
            elif attr_type == int:
                if isinstance(value, str):
                    converted_value = int(value)
                elif isinstance(value, float):
                    converted_value = round(value)
            elif attr_type == float:
                if isinstance(value, str) or isinstance(value, int):
                    converted_value = float(value)
            elif attr_type == bool:
                if isinstance(value, str):
                    converted_value = value.lower() not in ['false', '0', '', 'none', 'null']
                if isinstance(value, int) or isinstance(value, float):
                    converted_value = value != 0
                else:
                    converted_value = value is not None
            elif issubclass(attr_type, set) and isinstance(value, Iterable):
                converted_value = set(value)
            elif issubclass(attr_type, list) and isinstance(value, Iterable):
                converted_value = list(value)
            elif issubclass(attr_type, dict):
                if isinstance(value, str):
                    converted_value = json.loads(value)
                elif isinstance(value, DataJson):
                    converted_value = value.data_dict()
            elif issubclass(attr_type, DataJson):
                if isinstance(value, str) or isinstance(value, dict):
                    converted_value = DataJson.get_obj(value)
            elif issubclass(attr_type, Enum) and not isinstance(value, Enum):
                enum_cls = attr_type
                if isinstance(value, str):
                    value = value.lower()
                converted_value = enum_cls(value)
            else:
                raise AttributeError(f'Value {value} of wrong format for key: {attr.name}')
        return converted_value

    def __setattr__(self, key: str, value: Any) -> None:
        """

        """
        readonly_keys = self.get_attr_keys('readonly')
        

        if key in readonly_keys:
            return
        
        attr = getattr(self, key, None)
        if attr is None:
            return
        
        converted_value = self.convert_value_by_attr_type(attr, value)
        
        super().__setattr__(key, value)

    @classmethod
    def get_select(cls, with_ref_names: bool = True) -> Select:
        if cls.db_session is None:
            raise DatabaseError(f'{cls} db_session is not valid {cls.db_session}')
        pk_attrs = cls.get_attrs('pk')
        if not pk_attrs:
            raise AttributeError(f'Primary key not defined in {cls} attr_info')
        visible_attrs = cls.get_attrs('visible')
        query_attrs = pk_attrs | visible_attrs
        if with_ref_names:
            ref_name_attrs = cls.get_attrs('ref_name')
            if ref_name_attrs:
                query_attrs |= ref_name_attrs
                stmt = select(*query_attrs).select_from(cls) # type: ignore
                for ref_name_attr in ref_name_attrs:
                    stmt = stmt.join(ref_name_attr.parent.class_)
                return stmt
        return select(*query_attrs) # type: ignore

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

if __name__ == '__main__':
    # 测试代码
    from .contract import Contract
    Base.model_map = {
        'contract': Contract
    }
    print(Base.model_map)
    print(Base.attr_info_keys)
