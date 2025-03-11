from typing import Any, Type
from datetime import date
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

def serialize_value(value: Any) -> Any:
    """
    将值序列化为可存储的值。

    参数:
    value (Any): 值。

    返回:
    Any: 序列化后的值。
    """
    srl_value = None
    if isinstance(value, Enum):
        srl_value = value.value
    elif isinstance(value, set):
        srl_value = [serialize_value(v) for v in value]
    elif isinstance(value, date):
        srl_value = value.isoformat()
    elif isinstance(value, dict):
        srl_value = {k: serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        srl_value = [serialize_value(v) for v in value]
    elif isinstance(value, tuple):
        srl_value = [serialize_value(v) for v in value]
    elif isinstance(value, JsonBase):
        srl_value = value.data_dict(serializable=True)
    else:
        srl_value = value
    return srl_value

from sqlalchemy.types import TypeDecorator, JSON
class JsonBaseType(TypeDecorator):
    impl = JSON

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.dumps()
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return JsonBase.get_obj(value)
        return value

class DataJsonMixin:
    """
    JSON数据模型基类，用于定义JSON数据模型的基本属性和方法。
    - 类属性:
        - _cls_type (str): 模型类的类型。
        - class_map (dict[str, JsonBase]): 模型类的映射。
        - attr_info_keys (dict[str, Any]): 模型类的属性信息。
    - 类方法:
        - loads(data_str: str) -> dict[str, Any]: 将JSON字符串转换为字典。
        - str_to_dict(data_str: str, class_map: dict[str, JsonBase] | None = None) -> dict[str, Any]: 将JSON字符串转换为字典。
        - get_type(jsonData: str | dict | None = None, default: Any = None) -> str | None: 获取JSON数据的类型。
        - convert_value_by_attr_type(attr_key: str, value: Any) -> Any: 根据属性类型转换值。
        - load_dict(obj) -> dict[str, Any]: 将表单JSON数据字符串转换为字典。
    """
    _cls_type: str = 'data_json_mixin'
    """
    模型类的类型，str类型
    
    类型示例:
    - 'base'：基本父类
    - 'entity'：合同实体条款
    - 'scope'：合同范围条款
    - 'expiry': 合同到期条款
    """
    class_map: dict[str, Type['DataJsonMixin']] = {}
    """
    模型类的映射，dict类型，建议在JsonBase类使用前定义该变量

    映射示例:
    - {
        'base': JsonBase,
        'entity': ClauseEntity,
        'scope': ClauseScope,
        'expiry': ClauseExpiry
    }
    """
    attr_info_keys: dict[str, Any] = {
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
    模型类的属性信息，dict类型，建议在JsonBase类使用前定义该变量

    属性信息示例:
    - data: 需要存储的数据属性，不包括不需要存储的属性
    - required: 必需赋值的属性
    - readonly: 只读属性
    - hidden: 不需要显示给用户的属性
    - date: 日期属性
    - enum: 枚举属性
    - json: JSON属性
    - ref_map: 外键映射
    """
    def init_obj(self, data: str | dict | None = None, **kwargs):
        """
        初始化模型实例。
        
        参数:
        **kwargs: 模型实例的属性。
        """
        try:
            # 如果指定了序列化的字符串数据，则先读取序列化的数据到实例中
            data_dict = {}
            if isinstance(data, str):
                data_dict = json.loads(data)
            elif isinstance(data, dict):
                data_dict = data
            elif data is None:
                pass
            else:
                raise ValueError(f'Invalid data type for {self} in __init__')
            if kwargs is not None:
                data_dict.update(kwargs)
            data_dict = self.load_dict(data_dict)
            self.__dict__.update(data_dict)
        except Exception as e:
            logger.error(f'Error in __init__: {e}')

    @classmethod
    def loads(cls, data_str: str) -> dict[str, Any]:
        """
        将JSON字符串转换为字典。

        参数:
        data_str (str): JSON字符串。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        return json.loads(data_str, object_hook=cls.load_dict)
    
    def dumps(self) -> str:
        """
        将模型实例转换为JSON字符串。

        返回:
        str: 转换后的JSON字符串。
        """
        return json.dumps(self.data_dict(serializable=True))
    
    @classmethod
    def load_dict(cls, obj: dict) -> dict[str, Any]:
        """
        将表单JSON数据字符串转换为字典。
        - 如果JSON数据对应的JsonBase模型类必需属性缺失，抛出异常。
        - 如果JSON数据对应JsonBase模型类只读属性，则忽略只读属性。
        - 如果JSON数据有冗余，不会抛出异常，但冗余部分无法进行类型转换。

        参数:
        obj (dict): 表单数据的 JSON 字典。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        try:
            _cls_type = obj.get('_cls_type', None)
            # 如果_cls_type不存在或不在class_map中，或json_class是空值，抛出异常
            if _cls_type is None:
                return obj
            else:
                json_cls = cls.class_map.get(_cls_type, None)
                if _cls_type not in cls.class_map or json_cls is None:
                    raise AttributeError(f'No valid json_class for {_cls_type} in class_map {cls.class_map}')
            
            data_keys = cls.attr_info_keys.get('data', set())

            for key in data_keys:
                value = obj.get(key, None)
                if key in obj:
                    obj[key] = json_cls.convert_value_by_attr_type(key, value)
        except Exception as e:
            logger.error(f'Error in loading json string {obj} \n {e}')
        return obj

    @classmethod
    def get_obj(cls, jsonData: str | dict, default: Any = None) -> Any:
        """
        获取JSON数据的引用类。

        参数:
        jsonData (str | dict): JSON数据，可以是字符串或字典。
        default (Any): 默认值。

        返回:
        Type[JsonBase] | None: 引用类，如果未找到则返回None。
        """
        try:
            if jsonData is None:
                return default
            elif isinstance(jsonData, str):
                data_dict = json.loads(jsonData)
            elif isinstance(jsonData, dict):
                data_dict = jsonData
            else:
                return default
            cls_type = str(data_dict.get('_cls_type', None))
            if cls_type is None:
                raise TypeError(f'_cls_type not found in jsonData: {jsonData}')
            json_cls = cls.class_map.get(cls_type, None)
            if json_cls is None:
                raise AttributeError(f'json_cls not found in class_map of {cls} for _cls_type: {cls_type}')
            return json_cls(**data_dict)
        except Exception as e:
            logger.error(f'Error in {cls}.get_ref_cls: {e}')

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
        converted_value = value
        try:
            data_keys = cls.attr_info_keys.get('data', set())
            
            if attr_key in data_keys:
                # 获取attr_key为名的类属性
                attr = getattr(cls, attr_key, None)
                # 判断值是否为字符串格式（最常见）
                is_str = isinstance(value, str)
                # 转化字符串格式的日期为日期类型
                if isinstance(attr, date):
                    if is_str:
                        converted_value = date.fromisoformat(value)
                    elif isinstance(value, date):
                        converted_value = value
                    else:
                        raise AttributeError(f'Wrong date format for key: {attr_key}')
                elif isinstance(attr, int) and not isinstance(value, int):
                    converted_value = int(value)
                elif isinstance(attr, float) and not isinstance(value, float):
                    converted_value = float(value)
                elif isinstance(attr, bool) and not isinstance(value, bool):
                    if is_str:
                        converted_value = value.lower() not in ['false', '0', '', 'none', 'null']
                    if isinstance(value, int) or isinstance(value, float):
                        converted_value = value != 0
                    else:
                        converted_value = value is not None
                elif isinstance(attr, set) and not isinstance(value, set):
                    converted_value = set(value) # type: ignore
                elif isinstance(attr, list) and not isinstance(value, list):
                    converted_value = list(value) # type: ignore
                elif isinstance(attr, dict) and not isinstance(value, dict):
                    converted_value = json.loads(value) # type: ignore
                elif issubclass(attr.__class__, JsonBase) and not issubclass(value.__class__, JsonBase):
                    if is_str or isinstance(value, dict):
                        converted_value = JsonBase.get_obj(value)
                    else:
                        raise ValueError(f'Value parsing error for JsonBase class attribute {attr_key} and value is {value}')
                elif issubclass(attr.__class__, Enum) and not issubclass(value.__class__, Enum):
                    enum_cls = attr.__class__
                    converted_value = enum_cls(value)
        except Exception as e:
            logger.error(f'Error in convert_value_by_attr_type: {e}')
        return converted_value
    
    def data_dict(self, serializable: bool | None = False) -> dict[str, Any]:
        """
        将模型实例转换为字典。

        参数:
        serializable (bool | None): 是否序列化。

        返回:
        dict[str, Any]: 包含模型实例数据的字典。
        """
        data_keys = self.attr_info_keys.get('data', [])
        data_dict = {'_cls_type': self._cls_type}
        for key, value in self.__dict__.items():
            if key in data_keys:
                attr = getattr(self, key, None)
                if attr is not None:
                    data_dict.update({key: serialize_value(value) if serializable else value})
        return data_dict

class JsonBase():
    """
    JSON数据模型基类，用于定义JSON数据模型的基本属性和方法。
    - 类属性:
        - _cls_type (str): 模型类的类型。
        - class_map (dict[str, JsonBase]): 模型类的映射。
        - attr_info_keys (dict[str, Any]): 模型类的属性信息。
    - 类方法:
        - loads(data_str: str) -> dict[str, Any]: 将JSON字符串转换为字典。
        - str_to_dict(data_str: str, class_map: dict[str, JsonBase] | None = None) -> dict[str, Any]: 将JSON字符串转换为字典。
        - get_type(jsonData: str | dict | None = None, default: Any = None) -> str | None: 获取JSON数据的类型。
        - convert_value_by_attr_type(attr_key: str, value: Any) -> Any: 根据属性类型转换值。
        - load_dict(obj) -> dict[str, Any]: 将表单JSON数据字符串转换为字典。
    """
    _cls_type: str = 'base'
    """
    模型类的类型，str类型
    
    类型示例:
    - 'base'：基本父类
    - 'entity'：合同实体条款
    - 'scope'：合同范围条款
    - 'expiry': 合同到期条款
    """
    class_map: dict[str, Type['JsonBase']] = {}
    """
    模型类的映射，dict类型，建议在JsonBase类使用前定义该变量

    映射示例:
    - {
        'base': JsonBase,
        'entity': ClauseEntity,
        'scope': ClauseScope,
        'expiry': ClauseExpiry
    }
    """
    attr_info_keys: dict[str, Any] = {
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
    模型类的属性信息，dict类型，建议在JsonBase类使用前定义该变量

    属性信息示例:
    - data: 需要存储的数据属性，不包括不需要存储的属性
    - required: 必需赋值的属性
    - readonly: 只读属性
    - hidden: 不需要显示给用户的属性
    - date: 日期属性
    - enum: 枚举属性
    - json: JSON属性
    - ref_map: 外键映射
    """
    def __init__(self, data: str | dict | None = None, **kwargs):
        """
        初始化模型实例。
        
        参数:
        data (str | dict | None): 序列化的数据。
        **kwargs: 模型实例的属性。
        """
        self.init_obj(data, **kwargs)

    def init_obj(self, data: str | dict | None = None, **kwargs):
        """
        初始化模型实例。
        
        参数:
        **kwargs: 模型实例的属性。
        """
        try:
            # 如果指定了序列化的字符串数据，则先读取序列化的数据到实例中
            data_dict = {}
            if isinstance(data, str):
                data_dict = json.loads(data)
            elif isinstance(data, dict):
                data_dict = data
            elif data is None:
                pass
            else:
                raise ValueError(f'Invalid data type for {self} in __init__')
            if kwargs is not None:
                data_dict.update(kwargs)
            data_dict = self.load_dict(data_dict)
            self.__dict__.update(data_dict)
        except Exception as e:
            logger.error(f'Error in __init__: {e}')

    @classmethod
    def loads(cls, data_str: str) -> dict[str, Any]:
        """
        将JSON字符串转换为字典。

        参数:
        data_str (str): JSON字符串。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        return json.loads(data_str, object_hook=cls.load_dict)
    
    def dumps(self) -> str:
        """
        将模型实例转换为JSON字符串。

        返回:
        str: 转换后的JSON字符串。
        """
        return json.dumps(self.data_dict(serializable=True))
    
    @classmethod
    def load_dict(cls, obj: dict) -> dict[str, Any]:
        """
        将表单JSON数据字符串转换为字典。
        - 如果JSON数据对应的JsonBase模型类必需属性缺失，抛出异常。
        - 如果JSON数据对应JsonBase模型类只读属性，则忽略只读属性。
        - 如果JSON数据有冗余，不会抛出异常，但冗余部分无法进行类型转换。

        参数:
        obj (dict): 表单数据的 JSON 字典。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        try:
            _cls_type = obj.get('_cls_type', None)
            # 如果_cls_type不存在或不在class_map中，或json_class是空值，抛出异常
            if _cls_type is None:
                return obj
            else:
                json_cls = cls.class_map.get(_cls_type, None)
                if _cls_type not in cls.class_map or json_cls is None:
                    raise AttributeError(f'No valid json_class for {_cls_type} in class_map {cls.class_map}')
            
            data_keys = cls.attr_info_keys.get('data', set())

            for key in data_keys:
                value = obj.get(key, None)
                if key in obj:
                    obj[key] = json_cls.convert_value_by_attr_type(key, value)
        except Exception as e:
            logger.error(f'Error in loading json string {obj} \n {e}')
        return obj

    @classmethod
    def get_obj(cls, jsonData: str | dict, default: Any = None) -> Any:
        """
        获取JSON数据的引用类。

        参数:
        jsonData (str | dict): JSON数据，可以是字符串或字典。
        default (Any): 默认值。

        返回:
        Type[JsonBase] | None: 引用类，如果未找到则返回None。
        """
        try:
            if jsonData is None:
                return default
            elif isinstance(jsonData, str):
                data_dict = json.loads(jsonData)
            elif isinstance(jsonData, dict):
                data_dict = jsonData
            else:
                return default
            cls_type = str(data_dict.get('_cls_type', None))
            if cls_type is None:
                raise TypeError(f'_cls_type not found in jsonData: {jsonData}')
            json_cls = cls.class_map.get(cls_type, None)
            if json_cls is None:
                raise AttributeError(f'json_cls not found in class_map of {cls} for _cls_type: {cls_type}')
            return json_cls(**data_dict)
        except Exception as e:
            logger.error(f'Error in {cls}.get_ref_cls: {e}')

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
        converted_value = value
        try:
            data_keys = cls.attr_info_keys.get('data', set())
            
            if attr_key in data_keys:
                # 获取attr_key为名的类属性
                attr = getattr(cls, attr_key, None)
                # 判断值是否为字符串格式（最常见）
                is_str = isinstance(value, str)
                # 转化字符串格式的日期为日期类型
                if isinstance(attr, date):
                    if is_str:
                        converted_value = date.fromisoformat(value)
                    elif isinstance(value, date):
                        converted_value = value
                    else:
                        raise AttributeError(f'Wrong date format for key: {attr_key}')
                elif isinstance(attr, int) and not isinstance(value, int):
                    converted_value = int(value)
                elif isinstance(attr, float) and not isinstance(value, float):
                    converted_value = float(value)
                elif isinstance(attr, bool) and not isinstance(value, bool):
                    if is_str:
                        converted_value = value.lower() not in ['false', '0', '', 'none', 'null']
                    if isinstance(value, int) or isinstance(value, float):
                        converted_value = value != 0
                    else:
                        converted_value = value is not None
                elif isinstance(attr, set) and not isinstance(value, set):
                    converted_value = set(value) # type: ignore
                elif isinstance(attr, list) and not isinstance(value, list):
                    converted_value = list(value) # type: ignore
                elif isinstance(attr, dict) and not isinstance(value, dict):
                    converted_value = json.loads(value) # type: ignore
                elif issubclass(attr.__class__, JsonBase) and not issubclass(value.__class__, JsonBase):
                    if is_str or isinstance(value, dict):
                        converted_value = JsonBase.get_obj(value)
                    else:
                        raise ValueError(f'Value parsing error for JsonBase class attribute {attr_key} and value is {value}')
                elif issubclass(attr.__class__, Enum) and not issubclass(value.__class__, Enum):
                    enum_cls = attr.__class__
                    converted_value = enum_cls(value)
        except Exception as e:
            logger.error(f'Error in convert_value_by_attr_type: {e}')
        return converted_value
    
    def data_dict(self, serializable: bool | None = False) -> dict[str, Any]:
        """
        将模型实例转换为字典。

        参数:
        serializable (bool | None): 是否序列化。

        返回:
        dict[str, Any]: 包含模型实例数据的字典。
        """
        data_keys = self.attr_info_keys.get('data', [])
        data_dict = {'_cls_type': self._cls_type}
        for key, value in self.__dict__.items():
            if key in data_keys:
                attr = getattr(self, key, None)
                if attr is not None:
                    data_dict.update({key: serialize_value(value) if serializable else value})
        return data_dict
