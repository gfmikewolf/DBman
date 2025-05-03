from datetime import date
from enum import Enum
import json
from typing import Any, Iterable
from sqlalchemy.orm.properties import ColumnProperty

def serialize_value(attr: Any) -> Any:
    """
    convert the `attr` to a serializable value according to its data type.
    """
    
    if isinstance(attr, ColumnProperty):
        attr_type = attr.type.python_type
    else:
        attr_type = type(attr)
    srl_value = None
    from .base import DataJson
    if isinstance(attr, set) or isinstance(attr, tuple):
        srl_value = [serialize_value(v) for v in attr]
    elif isinstance(attr, dict):
        srl_value = {k: serialize_value(v) for k,v in attr.items()}
    elif issubclass(attr_type, Enum):
        srl_value = attr.value
    elif attr_type == date:
        srl_value = attr.isoformat()
    elif issubclass(attr_type, DataJson):
        srl_value = attr.dumps()
    else:
        srl_value = attr
    return srl_value if srl_value is not None else ''

def convert_value_by_python_type(value: Any, python_type: Any) -> Any:
    """
    convert the `value` by the `python_type`.
    """
    from .base import DataJson
    if value is None or value == '':
        return None
    converted_value = value.strip() if isinstance(value, str) else value
    if isinstance(value, python_type):
        return value
    elif issubclass(python_type, date) and isinstance(value, str):
        converted_value = date.fromisoformat(value) if value else None
    elif issubclass(python_type, int) and isinstance(value, str):
        converted_value = python_type(value.replace(',', ''))
    elif issubclass(python_type, float) and (isinstance(value, str) or isinstance(value, int)):
        converted_value = python_type(value.replace(',', '')) if isinstance(value, str) else python_type(value)
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
    elif issubclass(python_type, Enum):
        converted_value = python_type[value]
    else:
        raise AttributeError(f'Value {value} ({type(value).__name__}) of wrong format for key: ({python_type.__name__})')
    return converted_value
