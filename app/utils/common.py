# app/utils/common.py
from copy import deepcopy
import os
from typing import Any
import json
from flask import current_app
from datetime import date

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

def get_translation_dict(lang_set: list[str], locales: list[str] = []) -> dict[str, dict[str, str]]:
    dir_list = [os.getcwd(), 'app', 'dbman_dict']
    base_dir = os.path.join(*dir_list)
    dbman_dict = {}
    
    if locales and lang_set:
        try:
            for lang in lang_set:
                lang_dict = dict()
                for locale in locales:
                    filepath = os.path.join(base_dir, f'{locale}_{lang}.json')
                    with open(filepath, 'r', encoding='utf-8') as f:
                        jsonData = json.load(f)
                    lang_dict.update(jsonData)
                dbman_dict[lang] = lang_dict
        except Exception as e:
            raise FileNotFoundError(f"Error {e} occurred while loading dbman_dict file: {filepath}") # type: ignore
    return dbman_dict

def _(input_text:str | None, is_spec:bool = False):
    if not input_text:
        return ''
    return current_app.config['TRANSLATOR'].translate(input_text, is_spec)