from typing import Any, Iterable
from datetime import date
from enum import Enum
import json
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

def serialize_value(value: Any) -> Any:
    """
    将值序列化为可存储为JSON的值。

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
    elif isinstance(value, DataJson):
        srl_value = value.data_dict(serializable=True)
    else:
        srl_value = value
    return srl_value

from sqlalchemy.types import TypeDecorator, JSON
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
        - class_map (dict[str, JsonBase]): 模型类的映射。
        - attr_info (dict[str, Any]): 模型类的属性信息。
    - 类方法:
        - loads(data_str: str) -> dict[str, Any]: 将JSON字符串转换为字典。
        - str_to_dict(data_str: str, class_map: dict[str, JsonBase] | None = None) -> dict[str, Any]: 将JSON字符串转换为字典。
        - get_type(jsonData: str | dict | None = None, default: Any = None) -> str | None: 获取JSON数据的类型。
        - convert_value_by_attr_type(attr_key: str, value: Any) -> Any: 根据属性类型转换值。
        - load_dict(obj) -> dict[str, Any]: 将表单JSON数据字符串转换为字典。
    """
    _cls_type: str = 'data_json'
    """
    模型类的类型，str类型
    
    类型示例:
    - 'base'：基本父类
    - 'entity'：合同实体条款
    - 'scope'：合同范围条款
    - 'expiry': 合同到期条款
    """
    class_map: dict[str, type['DataJson']] = {}
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
    def __init__(self, data: str | dict | None, **kwargs):
        data_dict = self.load(data, **kwargs)
        self.__dict__.update(data_dict)

    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
        """
        将JSON字符串转换为字典。

        参数:
        data_str (str): JSON字符串。

        返回:
        dict[str, Any]: 转换后的字典。
        """

        if isinstance(data, str):
            data_dict = json.loads(data)
        elif isinstance(data, dict):
            if kwargs:
                data_dict = deepcopy(data)
                data_dict.update(kwargs)
            else:
                data_dict = data
        elif data is None:
            data_dict = {}
            raise ValueError(f'Invalid data type for {cls} in init_obj')
        return cls.load_dict(data_dict or {})
    
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
        data_dict (dict): 原始数据。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        
        cls_type = data.get('_cls_type', None)
        
        if cls_type is None:
            data_json_cls = cls
            cls_type = cls._cls_type
        else:
            data_json_cls = cls.class_map.get(cls_type, None)
            if data_json_cls is None:
                raise AttributeError(f'No valid json_class for {cls_type} in class_map {cls.class_map}')
        
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
        data_keys = self.attr_info.get('data', [])
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
        获取JSON数据的DataJson类。

        参数:
        jsonData (str | dict): JSON数据，可以是字符串或字典。
        default (Any): 默认值。

        返回:
        Any 任何继承了DataJson的类。
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


if __name__ == '__main__':
    
    class ClauseAction(Enum):
        """
        { 'add', 'remove', 'update' }
        """
        ADD = 'add'
        REMOVE = 'remove'
        UPDATE = 'update'

    class ClauseEntity(DataJson):
        """
        attributes:
            action (ClauseAction): 
                - Add, Remove, Novate
            entity_id (int): 
                - map table entity
            old_entity_id (int | None): 
                - only used in Novation

        constraints:
            - action is required.
            - entity_id is required.
            - old_entity_id is required if action is Novate.
        """
        _cls_type = 'clause_entity'
        
        action: ClauseAction = ClauseAction.UPDATE
        entity_id: int = 0
        old_entity_id: int | None = 0
        records: DataJson | None = DataJson({})
        
        attr_info = {
            'data': {'action', 'entity_id', 'old_entity_id', 'records'},
            'required': {'action', 'entity_id'}
        }

        def __init__(self, data: str | dict | None, **kwargs):
            super().__init__(data, **kwargs)
        

    DataJson.class_map = {
        'clause_entity': ClauseEntity
    }
    clause2 = ClauseEntity('{"_cls_type": "clause_entity", "entity_id": 2.1, "action": "remove"}')

    clause1 = ClauseEntity({
        'action': 'adD',
        'entity_id': 1.6,
        'records': clause2
    })

    print(clause1.data_dict(serializable=True))
    
