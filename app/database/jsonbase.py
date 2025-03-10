from operator import is_
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

class JsonBase():
    """
    JSON数据模型基类，用于定义JSON数据模型的基本属性和方法。
    - 类属性:
        - class_type (str): 模型类的类型。
        - class_map (dict[str, JsonBase]): 模型类的映射。
        - attr_info_keys (dict[str, Any]): 模型类的属性信息。
    - 类方法:
        - loads(data_str: str) -> dict[str, Any]: 将JSON字符串转换为字典。
        - str_to_dict(data_str: str, class_map: dict[str, JsonBase] | None = None) -> dict[str, Any]: 将JSON字符串转换为字典。
        - get_type(jsonData: str | dict | None = None, default: Any = None) -> str | None: 获取JSON数据的类型。
        - convert_value_by_attr_type(attr_key: str, value: Any) -> Any: 根据属性类型转换值。
        - object_hook(obj) -> dict[str, Any]: 将表单JSON数据字符串转换为字典。
    """
    class_type: str = 'base'
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
        'ref_map': {}
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

    def __init__(self, **kwargs):
        """
        初始化模型实例。
        
        参数:
        **kwargs: 模型实例的属性。
        """
        try:
            data_keys = self.attr_info_keys.get('data', set())
            required_keys = self.attr_info_keys.get('required', set())
            for key in data_keys:
                value = kwargs.get(key, None)
                if value is None:
                    if key in required_keys:
                        raise AttributeError(f'Attribute {key} not found in Model {self}')
                    else:
                        continue
                value = self.convert_value_by_attr_type(key, value)
                setattr(self, key, value)
        except Exception as e:
            logger.error(f'Error in __init__: {e}')

    @classmethod
    def loads(cls, data_str: str) -> dict[str, Any]:
        """
        将JSON字符串转换为字典。

        参数:
        data (str): JSON字符串。

        返回:
        Dict[str, Any]: 转换后的字典。
        """
        return json.loads(data_str, object_hook=cls.object_hook)
    
    def dumps(self) -> str:
        """
        将模型实例转换为JSON字符串。

        返回:
        str: 转换后的JSON字符串。
        """
        return json.dumps(self.data_dict(serializable=True))
    
    @classmethod
    def object_hook(cls, obj: dict) -> dict[str, Any]:
        """
        将表单JSON数据字符串转换为字典
        - 如果JSON数据对应的JsonBase模型类必需属性缺失，抛出异常。
        - 如果JSON数据对应Jsonbase模型类只读属性，则忽略只读属性。
        - 如果JSON数据有冗余，不会抛出异常，但冗余部分无法进行类型转换

        - 参数:
        obj (dict): 表单数据的 JSON 字典。

        - 返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        try:
            class_type = obj.get('class_type', None)
            # 如果class_type不存在或不在class_map中，或json_class是空值，抛出异常
            if class_type is None:
                return obj
            else:
                json_cls = cls.class_map.get(class_type, None)
                if class_type not in cls.class_map or json_cls is None:
                    raise AttributeError(f'No valid json_class for {class_type} in class_map {cls.class_map}')
            
            data_keys = cls.attr_info_keys.get('data', set())

            for key in data_keys:
                value = obj.get(key, None)
                if key in obj:
                    obj[key] = json_cls.convert_value_by_attr_type(key, value)
        except Exception as e:
            logger.error(f'Error in loading json string {obj} \n {e}')
        return obj

    @classmethod
    def get_class_type(cls, jsonData: str | dict | None = None, default: Any = None) -> str | None:
        """
        获取JSON数据的类型。

        参数:
        jsonData (str | dict | None): JSON数据。

        返回:
        str | None: JSON数据的类型。
        """
        class_type = None if default is None else default
        try:
            if jsonData is None:
                class_type = cls.class_type
            elif isinstance(jsonData, str):
                class_type = json.loads(jsonData).get('class_type', None)
            elif isinstance(jsonData, dict):
                class_type = jsonData.get('type', None)
        except Exception as e:
            logger.error(f'Error in get_type: {e}')
        return class_type

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
            date_keys = cls.attr_info_keys.get('date', set())
            
            if attr_key in data_keys:
                # 获取attr_key为名的类属性
                attr = getattr(cls, attr_key, None)
                is_str = isinstance(value, str)
                if attr_key in date_keys and is_str:
                    converted_value = date.fromisoformat(value)
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
                    converted_value = set(value)
                elif isinstance(attr, list) and not isinstance(value, list):
                    converted_value = list(value)
                elif isinstance(attr, dict) and not isinstance(value, dict):
                    converted_value = json.loads(value)
                elif issubclass(attr.__class__, JsonBase) and not issubclass(value.__class__, JsonBase):
                    json_cls = attr.__class__
                    converted_value = json_cls.object_hook(value)
                elif issubclass(attr.__class__, Enum) and not issubclass(value.__class__, Enum):
                    enum_cls = attr.__class__
                    converted_value = enum_cls(value)
        except Exception as e:
            logger.error(f'Error in convert_value_by_attr_type: {e}')
        return converted_value
    
    def data_dict(self, serializable: bool | None = False) -> dict[str, Any]:
        """
        将模型实例转换为字典。

        返回:
        dict[str, Any]: 包含模型实例数据的字典。
        """
        data_keys = self.attr_info_keys.get('data', [])
        data_dict = {'class_type': self.class_type}
        for key, value in self.__dict__.items():
            if key in data_keys:
                attr = getattr(self, key, None)
                if attr is not None:
                    data_dict.update({key: serialize_value(value) if serializable else value})
        return data_dict

# 测试用例
if __name__ == "__main__":
    # 设置日志级别为DEBUG，以便查看详细日志
    logging.basicConfig(level=logging.DEBUG)
    class Status(Enum):
        ACTIVE = 'active'
        INACTIVE = 'inactive'
    # 定义一个测试类，继承自JsonBase
    class TestJsonBase(JsonBase):
        class_type = 'test'
        attr_info_keys = {
            'data': {'name', 'age', 'birthdate', 'status', 'kids', 'parents', 'info'},
            'required': {'name', 'age'},
            'date': {'birthdate'},
            'enum': {'status'}
        }

        name: str = ''
        age: int = 0
        birthdate: date | None = date(1981,12,5)
        status: Status | None = Status.ACTIVE
        kids: set[int] | None = {0, 1, 2, 4}
        parents: list[str] | None = ['pa', 'ma']
        info: Type['TestJsonBase'] | None = None

    JsonBase.class_map = {'test': TestJsonBase}
    # 测试__init__方法
    test_instance = None
    try:
        test_instance = TestJsonBase(
            name="John Doe", 
            age='30', 
            birthdate="1990-01-01", 
            status='active', 
            kids = {0, 1}, 
            parents= ['papa', 'mama'], 
            info={
                'name': 'info1', 
                'age': 30.0, 
                'status': 'inactive',
                'birthdate': '2021-01-01',
                'kids': {2,3,4},
                'parents': ['a', 'b'],
                'class_type': 'test'
            }
        )
        print("\nInitialization successful:", test_instance.__dict__)
    except Exception as e:
        print("\nInitialization failed:", e)

    # 测试loads方法
    json_str = '{"class_type": "test", "name": "Jane Doe", "age": 25, "birthdate": "1995-05-15", "status": "inactive"}'
    if test_instance is not None:
        json_str = test_instance.dumps()
    print("\nJSON string:", json_str)
    try:
        loaded_data = TestJsonBase.loads(json_str)
        print("\nLoaded data:", loaded_data)
    except Exception as e:
        print("\nLoading failed:", e)

    # 测试dumps方法
    try:
        if test_instance is not None:
            json_output = test_instance.dumps()
            print("\nJSON dumps:", f'{json_output!r}')
    except Exception as e:
        print("\nDumps failed:", e)

    # 测试object_hook方法
    try:
        obj = {"class_type": "test", "name": "Jane Doe", "age": 25, "birthdate": "1995-05-15", "status": "inactive"}
        hooked_obj = TestJsonBase.object_hook(obj)
        print("\nObject hook result:", hooked_obj)
    except Exception as e:
        print("\nObject hook failed:", e)

    # 测试get_class_type方法
    try:
        class_type = TestJsonBase.get_class_type(json_str)
        print("\nClass type:", class_type)
    except Exception as e:
        print("\nGet class type failed:", e)

    # 测试convert_value_by_attr_type方法
    try:
        converted_value = TestJsonBase.convert_value_by_attr_type('status', 'active')
        print("\nConverted value:", converted_value)
    except Exception as e:
        print("\nConvert value by attr type failed:", e)

    # 测试to_dict方法
    try:
        if test_instance is not None:
            dict_output = test_instance.data_dict()
            print("\nDict output:", dict_output)
    except Exception as e:
        print("\nTo dict failed:", e)
