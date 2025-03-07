# utils/type_tools.py
from typing import Any
from datetime import date, datetime
# 类型转换等通用函数
def convert_string_by_attr_type(attr: Any, value: str) -> Any:
    converted_value = None
    try:
        if isinstance(attr, date):
            converted_value = datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(attr, int):
            converted_value = int(value)
        elif isinstance(attr, float):
            converted_value = float(value)
    except Exception:
        return None
    return converted_value if converted_value is not None else value
