# app.database.datajson.py
"""
数据JSON类的基类，提供类、字典、序列化字符串与json类型的转换

可引用的成员：
- serialize_value(value: Any) -> Any
    将数据转化为可序列化的类型
- class DataJsonType
    类修饰器，转换类实例与Json字符串
- class DataJson
    JSON数据模型基类，用于定义JSON数据模型的基本属性和方法。
"""
from typing import Any, Iterable
from datetime import date
from enum import Enum
import json
from copy import deepcopy
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import ColumnProperty

def serialize_value(attr: Any) -> Any:
    """
    将值序列化为可存储为JSON的值。

    参数:
    value (Any): 值。

    返回:
    Any: 序列化后的值。
    """
    if isinstance(attr, ColumnProperty):
        attr_type = attr.type.python_type
    else:
        attr_type = type(attr)
    srl_value = None
    if isinstance(attr, list) or isinstance(attr, tuple) or isinstance(attr, list):
        srl_value = [serialize_value(v) for v in attr]
    elif isinstance(attr, dict):
        srl_value = {k: serialize_value(v) for k,v in attr.items()}
    elif issubclass(attr_type, Enum):
        srl_value = attr.value
    elif attr_type == date:
        srl_value = attr.isoformat()
    elif issubclass(attr_type, DataJson):
        srl_value = attr.data_dict(serializable=True)
    else:
        srl_value = attr
    return srl_value

class DataJsonType(TypeDecorator):
    """
    JsonBase类修饰器，转换类实例与Json字符串
    """
    impl = JSON

    # 将DataJson类通过自有dumps()方法转换为字符串
    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.dumps()
        return value

    # 将DataJson字符串通过自有get_obj()方法转换为类
    def process_result_value(self, value, dialect):
        if value is not None:
            return DataJson.get_obj(value)
        return value

class DataJson:
    """
    JSON数据模型基类，用于定义JSON数据模型的基本属性和方法。
    - 类属性:
        - _cls_type (str): 模型类的类型。
        - class_map (dict[str, type['DataJson']]): 模型类的映射。
        - attr_info (dict[str, Any]): 模型类的属性信息。
    - 类方法:
        - load(data: dict | str | None = None, **kwargs) -> dict[str, Any]: 将JSON字符串或字典转换为字典。
        - load_dict(data: dict) -> dict[str, Any]: 将字典中对应attr_info里'data'类型的数据按_cls_type的类属性进行数据类型转换。
        - convert_value_by_attr_type(attr_key: str, value: Any) -> Any: 根据属性类型转换值。
        - get_obj(data: str | dict, default: Any = None) -> 'DataJson': 获取JSON数据的DataJson类实例。
    """
    _cls_type = 'data_json'
    """
    模型类的类型，str类型
    
    类型示例:
    - 'data_json'：基本父类
    - 'clause_entity'：合同实体条款
    - 'clause_scope'：合同范围条款
    - 'clause_expiry': 合同到期条款
    """

    class_map: dict[str, type['DataJson']] = {}
    """
    模型类的映射，dict类型，建议在DataJson类使用前定义该变量

    映射示例:
    - {
        'base': DataJson,
        'entity': ClauseEntity,
        'scope': ClauseScope,
        'expiry': ClauseExpiry
    }
    """

    attr_info: dict[str, Any] = {
        'data': set(),
        'required': set(),
        'readonly': set(),
        'hidden': set(),
        'date': set(),
        'enum': set(),
        'json': set(),
        'ref_map': dict
    }
    """
    模型类的属性信息，dict类型，建议在DataJson类使用前定义该变量

    必需的属性信息:
    - data: 需要存储的数据属性: str

    可选的属性信息
    - required: 必需赋值的属性: str
    - readonly: 只读属性: str
    - hidden: 不需要显示给用户的属性: str
    - foreignkeys: 外键信息: dict
        - model: 引用的数据库模型: Base
        - id: 引用的数据库模型键: ColumnProperty
        - name: 引用的数据库模型表征名称: ColumnProperty
        - order_by: list[ColumnProperty | ColumnClause] 如 [Contract.name.desc()]
    """
    def __init__(self, data: str | dict | None = None, **kwargs):
        data_dict = self.load(data, **kwargs)
        self.__dict__.update(data_dict)

    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
        """
        将JSON字符串或字典转换为字典。

        参数:
        data (dict | str | None): JSON字符串或字典。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        if data is None:
            data_dict = {}
        elif isinstance(data, str):
            data_dict = json.loads(data)
        elif isinstance(data, dict):
            if kwargs:
                data_dict = deepcopy(data) # 防止load函数修改用户data原始数据
            else:
                data_dict = data
        else:
            raise ValueError(f'Invalid data type for {cls} in {cls}.load(data={data}, kwargs={kwargs})')
        if kwargs:
            data_dict.update(kwargs)

        if not data_dict:
            return data_dict
        else:
            return cls.load_dict(data_dict)
    
    def dumps(self) -> str:
        """
        将模型实例转换为JSON字符串。

        返回:
        str: 转换后的JSON字符串。
        """
        return json.dumps(self.data_dict(serializable=True))
    
    @classmethod
    def load_dict(cls, data: dict) -> dict[str, Any]:   
        """
        将字典中对应attr_info里'data'类型的数据按_cls_type的类属性进行数据类型转换。
        - 如果数据缺失'required'属性，抛出属性异常。
        - 忽略'readonly'键的数据

        参数:
        data (dict): 原始数据。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        if cls._cls_type == 'data_json':
            cls_type = data.get('_cls_type', None)
            data_json_cls = cls.class_map.get(cls_type, None)
            if data_json_cls is None:
                raise AttributeError(f'No valid json_class for {cls_type} in class_map {cls.class_map}')
        else:
            cls_type = cls._cls_type
            data_json_cls = cls
                  
        data_keys = data_json_cls.attr_info.get('data', set())
        required_keys = data_json_cls.attr_info.get('required', set())
        # 找到required_keys中不存在data.keys()的键
        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise AttributeError(f'Missing required keys: {missing_keys} in data: {data}')
        
        # 在遍历前去掉data_keys中readonly的键
        readonly_keys = data_json_cls.attr_info.get('readonly', set())
        data_keys -= readonly_keys

        data_dict = {}
        data_dict['_cls_type'] = cls_type
        
        for data_key in data_keys:
            value = data.get(data_key, None)
            if data_key in data:
                data_dict[data_key] = data_json_cls.convert_value_by_attr_type(data_key, value)
        return data_dict

    @classmethod
    def convert_value_by_attr_type(cls, attr_key: str, value: Any) -> Any:
        """
        根据属性类型转换值。如果value不在data_keys中，不进行转换。

        参数:
        attr_key (str): 属性键。
        value (Any): 属性值。

        返回:
        Any: 转换后的属性值。
        """
        
        data_keys = cls.attr_info.get('data', set())
        converted_value = value
        if attr_key in data_keys:
            # 获取attr_key为名的类属性
            attr = getattr(cls, attr_key, None)
            # 转化字符串格式的日期为日期类型
            if type(attr) == type(value):
                return value
            if isinstance(attr, date) and isinstance(value, str):
                converted_value = date.fromisoformat(value)
            elif isinstance(attr, int):
                if isinstance(value, str):
                    converted_value = int(value)
                elif isinstance(value, float):
                    converted_value = round(value)
            elif isinstance(attr, float):
                if isinstance(value, str) or isinstance(value, int):
                    converted_value = float(value)
            elif isinstance(attr, bool):
                if isinstance(value, str):
                    converted_value = value.lower() not in ['false', '0', '', 'none', 'null']
                if isinstance(value, int) or isinstance(value, float):
                    converted_value = value != 0
                else:
                    converted_value = value is not None
            elif isinstance(attr, set) and isinstance(value, Iterable):
                converted_value = set(value)
            elif isinstance(attr, list) and isinstance(value, Iterable):
                converted_value = list(value)
            elif isinstance(attr, dict):
                if isinstance(value, str):
                    converted_value = json.loads(value)
                elif isinstance(value, DataJson):
                    converted_value = value.data_dict()
            elif isinstance(attr, DataJson):
                if isinstance(value, str) or isinstance(value, dict):
                    converted_value = DataJson.get_obj(value)
            elif isinstance(attr, Enum) and not isinstance(value, Enum):
                enum_cls = type(attr)
                if isinstance(value, str):
                    value = value.lower()
                converted_value = enum_cls(value)
            else:
                raise AttributeError(f'Value {value} of wrong format for key: {attr_key}')     
        return converted_value
    
    def data_dict(self, serializable: bool = False) -> dict[str, Any]:
        """
        将模型实例转换为字典。

        参数:
        serializable (bool): 是否将值序列化以便存储为JSON。

        返回:
        dict[str, Any]: 包含模型实例数据的字典。
        """
        data_keys = self.attr_info.get('data', {})
        data_dict = {'_cls_type': self._cls_type}
        for key, value in self.__dict__.items():
            if key in data_keys:
                attr = getattr(self, key, None)
                if attr is not None:
                    data_dict.update({key: serialize_value(value) if serializable else value})
        return data_dict
    
    @classmethod
    def get_obj(cls, data: str | dict, default: Any = None) -> 'DataJson':
        """
        获取JSON数据的DataJson类实例。

        参数:
        data (str | dict): JSON数据，可以是字符串或字典。
        default (Any): 默认值。

        返回:
        DataJson: 任何继承了DataJson的类实例。
        """

        data_dict = DataJson.load(data)
        if not data_dict:
            return default
        
        cls_type = data_dict.get('_cls_type', None)
        if cls_type is None:
            raise TypeError(f'_cls_type not found in jsonData: {data}')
        data_json_cls = cls.class_map.get(cls_type, None)
        if data_json_cls is None:
            raise AttributeError(f'json_cls not found in class_map of {cls} for _cls_type: {cls_type}')
        return data_json_cls(data_dict) # type: ignore

