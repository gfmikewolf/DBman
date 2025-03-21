# app.database.datajson.py

__all__ = ['DataJson', 'DataJsonType', 'serialize_value']
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
from typing import Any, Iterable, Optional
from datetime import date
from enum import Enum
import json

from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import ColumnProperty

from app.utils.common import args_to_dict

def serialize_value(attr: Any) -> Any:
    """
    将变量转换为可序列化为存储为JSON的数据类型。可适配ColumnProperty属性。

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
        srl_value = attr.data_dict(serializeable=True)
    else:
        srl_value = attr
    return srl_value if srl_value is not None else ''

def convert_value_by_python_type(value: Any, python_type: Any) -> Any:
    """
    根据python类型转换值。

    参数:
    value (Any): 值。
    python_type (Any): Python类型。

    返回:
    Any: 转换后的值。
    """
    if value is None:
        return None
    converted_value = value
    if isinstance(value, python_type):
        return value
    elif issubclass(python_type, date) and isinstance(value, str):
        converted_value = date.fromisoformat(value)
    elif issubclass(python_type, int) and isinstance(value, str):
        converted_value = python_type(value)
    elif issubclass(python_type, float) and (isinstance(value, str) or isinstance(value, int)):
        converted_value = python_type(value)
    elif issubclass(python_type, bool) and (isinstance(value, str) or isinstance(value, int) or isinstance(value, float)): 
        if isinstance(value, str):
            converted_value = value.lower() not in ['false', '0', '', 'none', 'null']
        if isinstance(value, int) or isinstance(value, float):
            converted_value = value != 0
    elif (issubclass(python_type, set) or issubclass(python_type, list)) and isinstance(value, Iterable):
        converted_value = python_type(value)
    elif issubclass(python_type, dict) and (isinstance(value, str) or isinstance(value, DataJson)):
        if isinstance(value, str):
            converted_value = json.loads(value)
        elif isinstance(value, DataJson):
            converted_value = value.data_dict()
    elif issubclass(python_type, DataJson) and (isinstance(value, str) or isinstance(value, dict)):
        converted_value = DataJson.get_obj(value)
    elif issubclass(python_type, Enum) and (isinstance(value, str) or isinstance(value, int)):
        if isinstance(value, str):
            value = value.lower()
        converted_value = python_type(value)
    else:
        raise AttributeError(f'Value {value} ({type(value).__name__}) of wrong format for key: ({python_type.__name__})')
    return converted_value

class DataJsonType(TypeDecorator):
    """
    JsonBase类修饰器，转换类实例与Json字符串
    """
    impl = JSON
    cache_ok = True

    @property
    def python_type(self):
        return DataJson

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
        - __datajson_id__ (str): 模型类的类型id，子类必须实例化这个属性。
        - class_map (dict[str, type['DataJson']]): 模型类的映射。
        - attr_info (dict[str, Any]): 模型类的属性信息。
    
    公共方法：
        - 类方法:
            - load(data: dict | str | None = None, **kwargs) -> dict[str, Any]: 将JSON字符串或字典转换为字典。
            - get_cls_from_dict(data: dict[str, Any]) -> type['DataJson'] | None: 根据字典获取模型类。
            - convert_value_by_attr_type(value: Any, attr_key: str) -> Any: 根据属性类型转换值。
            - get_keys(*args: str) -> set[str]: 获取包含指定信息的属性的键集合。
            - get_obj(data: str | dict, **kwargs: Any) -> Optional['DataJson']: 获取JSON数据的DataJson类实例。
        - 实例方法:
            - __init__(self, data: str | dict | None = None, **kwargs): 初始化模型实例。
            - dumps(self) -> str: 将模型实例转换为JSON字符串。
            - data_dict(self, serializeable: bool = False) -> dict[str, Any]:
    
    私有方法：
        - 类方法:
            - _load_dict(cls, data: dict) -> dict[str, Any]: 将字典中对应attr_info里'data'类型的数据按类属性进行数据类型转换。
    """
    __datajson_id__ = NotImplemented
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

    attr_info: dict[str, Any] = NotImplemented
    """
    模型类的属性信息，dict类型，建议在DataJson类使用前定义该变量

    必需的属性信息:
    - data: 需要存储的数据属性: str

    可选的属性信息
    - required: 必需赋值的属性: str
    - readonly: 只读属性: str
    - hidden: 不需要显示给用户的属性: str
    - foreignkeys: 外键信息: dict
        - ref_table: 引用的数据表名称: str, 如 'contract'
        - ref_pk: 引用的数据库模型键: tuple[str,...] 如 ('contract_id',)
        - ref_name: 引用的数据库模型表征名称: str, 如 'contract_name'
        - order_by: 作为列表框供用户选择时选项的排序要求: tuple[str, ...] 如 ('contract_name', 'contract_fullname.desc')
    """
    def __init__(self, data: str | dict | None = None, **kwargs):
        data_dict = self.load(data, **kwargs)
        self.__dict__.update(data_dict)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.attr_info is NotImplemented:
            cls.attr_info = dict()

    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
        """
        将JSON字符串或字典转换为字典。

        参数:
        data (dict | str | None): JSON字符串或字典。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        args_dict = args_to_dict(data, **kwargs)
        data_json_cls = cls.get_cls_from_dict(args_dict)

        if  data_json_cls is None:
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {json_cls}')

        if not args_dict:
            return args_dict
        else:
            return data_json_cls._load_dict(args_dict)
    
    def dumps(self) -> str:
        """
        将模型实例转换为JSON字符串。

        返回:
        str: 转换后的JSON字符串。
        """
        return json.dumps(self.data_dict(serializeable=True))
    
    @classmethod
    def get_cls_from_dict(cls, data: dict[str, Any]) -> type['DataJson'] | None:
        if cls.__datajson_id__ is NotImplemented:
            datajson_id = data.get('__datajson_id__', None)
            data_json_cls = cls.class_map.get(datajson_id, None)
            if data_json_cls is None:
                raise AttributeError(f'Invalid {datajson_id} in class_map {cls.class_map}')
        else:
            datajson_id = 'data_json'
            data_json_cls = cls
        
        required_keys = data_json_cls.get_keys('required')
        # 找到required_keys中不存在于data.keys()的键
        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise AttributeError(f'Missing required keys: {missing_keys} in {data}')
        
        # 如果data_keys中有readonly的键，抛出属性异常
        readonly_keys = data_json_cls.get_keys('readonly')
        # 如果data_keys中有readonly_keys,下面的计算会得到非空集合
        if (readonly_keys - (readonly_keys - data.keys())):
            raise AttributeError(f'Readonly keys: {readonly_keys} in {data}')
        return data_json_cls

    @classmethod
    def _load_dict(cls, data: dict) -> dict[str, Any]:   
        """
        将字典中对应attr_info里'data'类型的数据按类属性进行数据类型转换。
        - 字典必须经过get_cls_from_dict()方法处理后才能调用该方法。

        参数:
        data (dict): 原始数据。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        data_json_cls = cls
        if cls.__datajson_id__ == NotImplemented:
            data_json_cls = cls.get_cls_from_dict(data)
            if data_json_cls is None:
                raise AttributeError(f'Invalid data: {data} to match {data_json_cls}')
        data_dict = {}
        data_dict['__datajson_id__'] = data_json_cls.__datajson_id__
        mod_keys = data_json_cls.get_keys('modifiable')

        for key in mod_keys:
            value = data.get(key, None)
            if value is not None:
                data_dict[key] = data_json_cls.convert_value_by_attr_type(value, key)
        return data_dict

    @classmethod
    def convert_value_by_attr_type(cls, value: Any, attr_key: str) -> Any:
        """
        根据属性类型转换值。如果value不在data_keys中，不进行转换。

        参数:
        attr_key (str): 属性键。
        value (Any): 属性值。

        返回:
        Any: 转换后的属性值。
        """
        attr = getattr(cls, attr_key, None)
        if attr is None:
            raise AttributeError(f'Attribute {attr_key} not found in {cls}')
        attr_type = type(attr)
        converted_value = convert_value_by_python_type(value, attr_type)    
        return converted_value
    
    def data_dict(self, serializeable: bool = False) -> dict[str, Any]:
        """
        将模型实例转换为字典。

        参数:
        serializeable (bool): 是否将值序列化以便存储为JSON。

        返回:
        dict[str, Any]: 包含模型实例数据的字典。
        """
        data_keys = self.get_keys('data')
        if self.__datajson_id__ is NotImplemented:
            djid = 'data_json'
        else:
            djid = self.__datajson_id__
        data_dict = {'__datajson_id__': djid}
        for key, value in self.__dict__.items():
            if key in data_keys:
                attr = getattr(self, key, None)
                if attr is not None:
                    data_dict.update({key: serialize_value(value) if serializeable else value})
        return data_dict
    
    @classmethod
    def get_obj(cls, data: str | dict, **kwargs: Any) -> Optional['DataJson']:
        """
        获取JSON数据的DataJson类实例。

        参数:
        data (str | dict): JSON数据，可以是字符串或字典。
        default (Any): 默认值。

        返回:
        DataJson: 任何继承了DataJson的类实例。
        """

        data_dict = args_to_dict(data, **kwargs)
        if not data_dict:
            return None
        
        if cls.__datajson_id__ is NotImplemented:
            datajson_id = data_dict.get('__datajson_id__', None)
            if datajson_id is None:
                raise TypeError(f'__datajson_id__ not found in jsonData: {data}')
            data_json_cls = cls.class_map.get(datajson_id, None)
            if data_json_cls is None:
                raise AttributeError(f'json_cls not found in class_map of {cls} for __datajson_id__: {datajson_id}')
        else:
            data_json_cls = cls

        return data_json_cls(data_dict)

    @classmethod
    def get_keys(cls, *args: str) -> set[str]:
        """
        获取包含指定信息的属性的键集合。
        
        参数:
        *args (str): 包含的信息字符串参数。
        
        返回:
        set[str]: 包含指定信息的键集合。
        """
        keys = set()
        for info in args:
            # 如果已经缓存了信息，返回缓存信息
            if info in cls.attr_info:
                keys.update(cls.attr_info[info])
            # 如果没有缓存信息，根据参数获取信息并缓存
            elif info in {'readonly', 'hidden', 'required', 'data', 'foreignkeys'}:
                info_keys = cls.attr_info.get(info, set())
                keys.update(info_keys)
            elif info == 'modifiable':
                info_keys = cls.get_keys('data') - cls.get_keys('readonly')
                cls.attr_info[info] = info_keys
                keys.update(info_keys)
            elif info == 'visible':
                info_keys = cls.get_keys('data') - cls.get_keys('hidden')
                cls.attr_info[info] = info_keys
                keys.update(info_keys)
            elif info in {'date', 'json', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_keys = set()
                for data_key in cls.get_keys('data'):
                    attr = getattr(cls, data_key, None)
                    if attr is None:
                        raise AttributeError(f'Attribute {data_key} not found in {cls}')
                    if isinstance(attr, eval(info)):
                        info_keys.add(data_key)
                cls.attr_info[info] = info_keys
                keys.update(info_keys)  
            else:
                raise AttributeError(f'Invalid key info {info} for {cls}')
        return keys
