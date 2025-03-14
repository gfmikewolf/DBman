# app/database/base.py
"""
Base 模块包含了 Base 类，该类是所有数据模型类的基类。
"""
import json
from sqlite3 import DatabaseError
from typing import Any, Iterable
from enum import Enum
from datetime import date
from sqlalchemy import (
    select, Select
)

from sqlalchemy.orm import (
    DeclarativeBase,
    ColumnProperty,
    scoped_session,
)
from copy import deepcopy
from .datajson import DataJson, serialize_value

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

    def update(self, data: str | dict | None = None, **kwargs: Any) -> None:
        """
        初始化模型实例。如果提供了 form_data，则使用表单数据初始化实例。

        参数:
        form_data (dict[str, str], 可选): 表单数据的字典，其中键是表单字段名，值是表单字段的值。
        """
        args_dict = Base._args_to_dict(data, **kwargs)
        if not self.validate_attr_dict(args_dict):
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {self}')
        mod_attrs = self.get_attrs('modifiable')
        for attr in mod_attrs:
            attr = args_dict[attr.name]
    
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
        *args (str): 包含的信息字符串参数。
        
        返回:
        set[ColumnProperty | Column] | tuple[Column | ColumnProperty, ...]: 包含指定信息的列属性集合。
        参数为'data'和'pk'时返回模型属性的元组，保持参数顺序，方便后续查询
        其他参数返回模型属性的集合
        """
        attrs = set()
        for info in args:
            if info in cls.attr_info:
                attrs.update(cls.attr_info[info])
            elif info == 'data':
                cached = set(cls.__mapper__.column_attrs)
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info == 'pk':
                cached = set(cls.__mapper__.primary_key)
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info == 'modifiable':
                cached = cls.get_attrs('data') - cls.get_attrs('readonly')
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info == 'visible':
                cached = cls.get_attrs('data') - cls.get_attrs('hidden')
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info in {'date', 'json', 'int', 'float', 'bool', 'set', 'list', 'dict'}:
                cached = set()
                for attr in cls.get_attrs('data'):
                    if isinstance(attr.type.python_type, eval(info)):
                        cached.add(attr)
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info in {'DataJson', 'Enum'}:
                cached = set()
                for attr in cls.get_attrs('data'):
                    if issubclass(attr.type.python_type, eval(info)):
                        cached.add(attr)
                cls.attr_info[info] = cached
                attrs.update(cached)
            elif info == 'fk':
                cached = set()
                for attr in cls.get_attrs('data'):
                    if attr.foreign_keys:
                        cached.add(attr)
                cls.attr_info[info] = cached 
                attrs.update(cached)   
            else:
                raise AttributeError(f'Invalid info {info} in {cls}')
        return attrs
    
    @classmethod
    def get_attr_keys(cls, *args: str) -> set[str]:
        attr_keys = set()
        for arg in args:
            keys = cls.attr_info_keys.get(arg, None)
            if not keys:
                attrs = cls.get_attrs(arg)
                keys = set(attr.name for attr in attrs)
                cls.attr_info_keys[arg] = keys
            attr_keys.update(keys)
        return attr_keys
    
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
        
        for data_attr in data_attrs:
            value = args_dict.get(data_attr.name, None)
            if data_attr in args_dict:
                data_dict[data_attr.name] = cls.convert_value_by_attr_type(data_attr, value)
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
        根据属性类型转换值。如果value不在data_attrs中，不进行转换。

        参数:
        attr (ColumnProperty): 属性键。
        value (Any): 属性值。

        返回:
        Any: 转换后的属性值。
        """    
        data_attrs = cls.get_attrs('data')
        converted_value = value
        if attr in data_attrs:
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
        readonly_keys = self.get_attr_keys('readonly')
        if key in readonly_keys:
            return
        
        attr = getattr(self, key, None)
        if attr is None:
            super().__setattr__(key, value)
            return
        
        converted_value = self.convert_value_by_attr_type(attr, value)
        super().__setattr__(key, converted_value)

    @classmethod
    def fetch_datatable(cls) -> dict[str, Any]:
        if cls.db_session is None:
            raise DatabaseError(f'{cls}.db_session is not valid.')
        pk_attrs = cls.get_attrs('pk')
        if not pk_attrs:
            raise AttributeError(f'Primary key not defined in {cls} attr_info')
        mapper = cls.__mapper__
        visible_attrs = cls.get_attrs('visible')
        query_cols = [attr.expression for attr in mapper.column_attrs if attr in visible_attrs | pk_attrs]
        joins = []
        ref_map = dict()
        for rel in cls.__mapper__.relationships:
            if rel.uselist:
                continue
            ref_model = rel.entity.class_
            if hasattr(ref_model, 'name'):
                ref_id_attr = getattr(ref_model, 'id', None)
                ref_name_attr = getattr(ref_model, 'name', None)
                ref_tablename = ref_model.__tablename__
                if not (ref_model is None or ref_id_attr is None or ref_name_attr is None):
                    ref_map[ref_name_attr.name] = (ref_tablename, ref_id_attr.name)
                    query_cols.extend([ref_name_attr.expression, ref_id_attr.expression])
                    visible_attrs.add(ref_name_attr)
                    joins.append(rel)
        query = select(*query_cols)
        if joins:
            query = query.join(*joins)
        
        datatable = dict()
        with cls.db_session() as sess:
            result = sess.execute(query).all()

        visible_keys = cls.get_attr_keys('visible')    
        datatable['headers'] = [key for key in result.keys() if key in visible_keys]
        datatable['data'] = []
        datatable['_pks'] = []
        datatable['ref_id'] = []
        datatable['ref_map'] = ref_map
        if not result:
            return datatable  
        
        pk_keys = cls.get_attr_keys('pk')
        json_keys = cls.get_attr_keys('DataJson', 'json')
        visible_keys = cls.get_attr_keys('visible')
        datatable['headers_json'] = json_keys - (json_keys - visible_keys)
        
        for row in result:
            datarow = []
            _pks = []
            for key in result.keys():
                if key in visible_keys:
                    datarow.append(row.get(key, ''))
                if key in pk_keys:
                    _pks.append(key)
            datatable['data'].append(datarow)
            datatable['_pks'].append(','.join(_pks))
            if ref_map:
                ref = dict()
                for ref_name, ref_table_id in ref_map.items():
                    ref.update({ref_name:row.get(ref_table_id[1])})
                datatable['ref_id'].append(ref)
        return datatable

    def data_dict(self, serializable: bool = False) -> dict[str, Any]:
        data_dict = {'__tablename__': self.__tablename__}
        data_keys = self.get_attr_keys('data')
        for data_key in data_keys:
            data_attr = getattr(self, data_key, None)
            if data_attr is None:
                raise AttributeError(f'Invalid attribute {data_key} for {self}')
            data_dict[data_attr.name] = serialize_value(data_attr) if serializable else data_attr
        return data_dict
