# utils/common.py
from copy import deepcopy
from typing import Any
import json

def args_to_dict(data: str | dict | None = None, **kwargs: Any) -> dict[str, Any]:
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
            data_dict = deepcopy(data) # 防止修改用户data原始数据
        else:
            data_dict = data
    else:
        raise ValueError(f'Invalid data type for arguments (data={data}, kwargs={kwargs})')
    if kwargs:
        data_dict.update(kwargs)
    return data_dict
