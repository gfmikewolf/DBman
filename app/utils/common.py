# utils/common.py
from copy import deepcopy
from typing import Any
import json

def args_to_dict(data: str | dict | None = None, **kwargs: Any) -> dict[str, Any]:
    """
    Convert arguments to a dictionary.
    .. note:: `kwargs` will override the values in `data` if the keys are the same.
    :return: A dictionary containing the arguments or an empty dictionary if no arguments are provided.
    :raise TypeError: If the data type is not supported.
    """
    if data is None:
        data_dict = {}
    elif isinstance(data, str):
        data_dict = json.loads(data)
    elif isinstance(data, dict):
        if kwargs and data:
            data_dict = deepcopy(data) # avoiding modifying the original data
        else:
            data_dict = data
    else:
        raise TypeError(f'Invalid data type for arguments (data={data}, kwargs={kwargs})')
    if kwargs:
        data_dict.update(kwargs)
    return data_dict

