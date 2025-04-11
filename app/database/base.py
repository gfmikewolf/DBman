# app/database/base.py

__all__ = ['Base', 'DataJson']

# python
from typing import Any, Optional
from datetime import date # in use eval('date')
from enum import Enum # in use eval('Enum')
import json
from abc import ABC, abstractmethod

# sqlalchemy
from sqlalchemy.orm import DeclarativeBase

# app
from app.utils.common import args_to_dict
from .utils import serialize_value, convert_value_by_python_type

class Base(DeclarativeBase):
    """
    Base class for all database models in the application.

    .. attention:: 
    - `model_map` shall be set before using the class and its subclasses.
    - rules for making subclass of Base:
        - table column name **MUST** be the same as the property name.
        - each subclass **MUST** have a _name property to represent itself.

    :cvar model_map: { database table name: Class name of the model }
    :cvar key_info: Dictionary and cache of column information valued by keys.
    :cvar rel_info: Dictionary of relationship information.
    """
    model_map: dict[str, type['Base']] = {}
    """
    a dictionary of model classes, used to identify the class from the __tablename__ key in the data dictionary.

    .. attention:: must be defined in the subclass before using its properties or methods.
    """

    key_info: dict[str, set[str] | tuple[str, ...]] = NotImplemented
    """
    Information about the columns in the database table.

    :key: 
    string, information type, including:
        - user-defined types: string, *readonly*, *hidden*, *required*
        - data types: string, *str*, *int*, *float*, *bool*, *set*, *list*, *dict*, *DataJson*, *Enum*
    
    :value: 
    a set of string for user-defined types and a dict for data types, or
    a dict for relationship map type `ref_map`, including the entries below:
        - `ref_map['ref_name_col']`: referenced name column name, e.g. *contract_name*
        - `ref_map['select_order']`: order by tuple of column name and order direction (asc or desc)

    .. attention:: - must be defined in the subclass before using its properties or methods.
                   - the return type of set of string has no order.
    """

    def __init__(self, **kwargs: Any):
        """
        set default values for all new instances
        """
        super().__init__()
        for key in self.get_keys('modifiable'):
            if key not in kwargs:
                cls = self.__class__
                prop = cls.__mapper__.columns.get(key)
                if prop is not None:
                    default = prop.default
                    if default and hasattr(default, 'arg'):
                        setattr(self, key, default.arg) # type: ignore
            else:
                setattr(self, key, kwargs.get(key))

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Initialize the class variables such as key_info.

        .. attention::  `key_info` is not implemented in the base class
                        but initialized in this method 
                        to create independent subclass level variables.
        """
        super().__init_subclass__(**kwargs)
        if cls.key_info is NotImplemented:
            cls.key_info = dict()

    def update_data(self, data: str | dict | None = None, **kwargs: Any) -> None:
        """
        Update the data of an instance with `data` and `kwargs`.
        if the instance is new, entries not specified will be filled with default values.
        if the instance exists in database, only entries in parameters will be updated.
        .. attention:: This method will only update the data in the instance.

        :param data: string or dict or none, json string or dict to be converted to DataJson object.
        :param kwargs: other keyword arguments which override the correspondent entries in parameter `data`.
        """
        args_dict = args_to_dict(data, **kwargs)
        mod_keys = self.get_keys('modifiable')
        json_keys = self.get_keys('DataJson')
        if args_dict.keys() - mod_keys: # check if there is any keys not modifiable
            raise KeyError(f'Invalid keys: {args_dict.keys() - mod_keys}')
        for key, value in args_dict.items():
            if key in json_keys:
                value = DataJson.get_obj(value)
            setattr(self, key, value)

    @classmethod
    def get_headers(cls) -> list[str]:
        """
        :return: a list of visible keys in the model.
        """
        cache = cls.key_info.get('headers', list())
        if not cache:
            cache = cls.key_info['headers'] = [key for key in cls.key_info.get('data') if key not in cls.get_keys('hidden')] # type: ignore
        return cache # type: ignore

    @classmethod
    def get_polymorphic_base(cls) -> type['Base'] | None:
        base_class = cls.__mapper__.base_mapper.class_
        if hasattr(base_class, '__mapper_args__') and base_class.__mapper_args__.get('polymorphic_on', None):
            return base_class
        else:
            return None
    
    @classmethod
    def get_polymorphic_key(cls) -> str:
        key = ''
        ma = getattr(cls, '__mapper_args__', None)
        if ma:
            polymorphic_attr = cls.__mapper_args__.get('polymorphic_on', None)
            if polymorphic_attr:
                key = polymorphic_attr.name
        return key
    
    @classmethod
    def get_col_rel_map(cls, polymorphic_spec_only=False) -> dict[str, str]:
        """
        :return: a dict of the single relationship map for the class.

        .. example::
        ```python
            { 'entity_id': 'entity', 'old_entity_id': 'old_entity' }
        ```
        """
        crm = dict()
        base_data_keys = set()
        if polymorphic_spec_only:
            base_data_keys = cls.get_keys('polybase_data')

        for r in cls.__mapper__.relationships:
            local_col_key = next(iter(r.local_columns)).key
            cond = (not r.uselist) and (r.secondary is None)
            if cond and local_col_key not in base_data_keys:
                crm[local_col_key] = r.key
        return crm
    
    @classmethod
    def get_keys(cls, *args: str) -> set[str]:
        """
        :return: a set keys of keys. 
        :param args: a list of information strings, including:

            - user-defined types: string, 'readonly', 'hidden', 'required', 'data', 'polybase_data'
            - data types: string, 'str', 'int', 'float', 'bool', 'set', 'list', 'dict', 'DataJson', 'Enum'
            - relationship types: 'single_rel', 'multi_rel'
            - other args: return the keys with property.info[arg] exists
        :raise AttributeError: if the information is not valid for this class.

        .. notes:: the information is cached after the first get.
        """
        keys = set()
        for info in args:
            if info in cls.key_info:
                info_keys = cls.key_info.get(info, set())
                if info == 'data':
                    info_keys = set(info_keys)
                keys.update(info_keys)
            elif info == 'polybase_data':
                info_keys = set()
                p_base = cls.get_polymorphic_base()
                if p_base:
                    info_keys = p_base.get_keys('data')
                    keys.update(info_keys)
                    cls.key_info[info] = info_keys
            elif info == 'pk':
                info_keys = set()
                for col in cls.__mapper__.primary_key:
                    info_keys.add(col.key)
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info == 'required':
                info_keys = set()
                for col in cls.__mapper__.columns:
                    # If the column is not nullable and not autoincrement, it is required.
                    if (not col.nullable) and (col.autoincrement is not True):
                        info_keys.add(col.key)
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info == 'modifiable':
                info_keys = cls.get_keys('data') - cls.get_keys('readonly')
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info == 'visible':
                info_keys = cls.get_keys('data') - cls.get_keys('hidden')
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info in {'date', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_keys = set()
                for key in cls.get_keys('modifiable'):
                    attr = getattr(cls, key)
                    if hasattr(attr, 'type') and hasattr(attr.type, 'python_type'):
                        if issubclass(attr.type.python_type, eval(info)):
                            info_keys.add(key)
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info in {'single_rel', 'multi_rel'}:
                info_keys = set()
                for rel in cls.__mapper__.relationships:
                    if rel.key in cls.get_keys('data'):
                        if rel.uselist and info == 'multi_rel' :
                            info_keys.add(rel.key)
                        elif not rel.uselist and info == 'single_rel':
                            info_keys.add(rel.key)
                cls.key_info[info] = info_keys 
                keys.update(info_keys)   
            else:
                info_keys = set()
                for key in cls.get_keys('data'):
                    attr = getattr(cls, key)
                    if hasattr(attr, 'info'):
                        if attr.info.get(info, None) is not None:
                            info_keys.add(key)
                cls.key_info[info] = info_keys
                keys.update(info_keys)
        return keys
    
    @classmethod
    def get_obj(cls, table_name: str, data: dict[str, Any]) -> 'Base':
        data_cls = cls.model_map.get(table_name, None)
        if data_cls is None:
            raise KeyError(f'{table_name} not in Base.model_map')
        if hasattr(data_cls, '__mapper_args__'):
            ma = data_cls.__mapper_args__
            if ma:
                id_on = ma.get('polymorphic_on')
                if id_on:
                    id_key = id_on.name
                    attr_type = getattr(data_cls, id_key).type.python_type
                    if issubclass(attr_type, Enum):
                        id_v = attr_type[data.get(id_key)] # type: ignore
                    else:
                        id_v = attr_type(data.get(id_key))
                    pm = data_cls.__mapper__.polymorphic_map
                    data_cls = pm.get(id_v).class_ # type: ignore
        conv_data = data_cls.convert_dict_by_attr_type(data) # type: ignore
        return data_cls(**conv_data)
    
    @classmethod
    def convert_dict_by_attr_type(cls, data: dict[str, Any]) -> dict[str, Any]:
        conv_data = dict()
        for key, value in data.items():
            converted_value = value
            if key in cls.get_keys('data'):
                readonly_keys = cls.get_keys('readonly')
                if key in readonly_keys:
                    raise AttributeError(f'Key {key} is readonly for {cls}')
                attr = getattr(cls, key, None)
                if attr is None:
                    raise AttributeError(f'Invalid key {key} for {cls}')
                if hasattr(attr, 'type') and hasattr(attr.type, 'python_type'):
                    converted_value = convert_value_by_python_type(value, attr.type.python_type)
                conv_data[key] = converted_value
        return conv_data
    
    def data_dict(self, serializeable: bool = False) -> dict[str, Any]:
        """
        :return: a dictionary containing data of the instance.
        :param serializeable: if True, the data is serialized to allowed types for JSON.
        """
        data_dict = {'__tablename__': self.__tablename__}
        for data_key in self.get_keys('data') - self.get_keys('single_rel'):
            value = getattr(self, data_key)
            if value is None and serializeable:
                data_dict[data_key] = ''
            elif serializeable:        
                data_dict[data_key] = serialize_value(value)
            else:
                data_dict[data_key] = value
        return data_dict  
    
    @classmethod
    def get_col_datajson_id_map(cls) -> dict[str, str]:
        """
        :return: dict {DataJson_local_col.key: DataJson_id_col.key }
        """
        ele_id_map = dict()
        for key in cls.get_keys('DataJson'):
            attr = getattr(cls, key)
            if hasattr(attr, 'info'):
                element_key = attr.info.get('DataJson_id_key', None)
                if element_key is None:
                    ele_id_map[key] = None
                else:
                    ele_id_map[element_key] = key

        return ele_id_map

class DataJson(ABC):
    """
    Base class for data of json type.
    """

    __datajson_id__ = NotImplemented
    """
    Unique identifier for the DataJson class. It is used to identify the class in the class_map.
    note: this variable must be defined in the subclass.
    """

    class_map: dict[str, type['DataJson']] = {}
    """
    Subclass map for DataJson classes. It is used to identify the subclass from the UID (__datajson_id__).
    
    **Should be defined before using the sub class.**

    :example: 

    class_map = {
        'entity': `ClauseEntity`,
        'scope': `ClauseScope`,
        'expiry': `ClauseExpiry`
    }
    """

    key_info: dict[str, tuple[str, ...] | set[str]] = NotImplemented
    """
    A dict of information regarding attributes of the class, including user-defined types and data types.

    .. attention::
    - Should be **defined in the subclass** before using its properties or methods.
    - **a set has no order.**
    
    :key: string, infomation type, including:
    - user-defined types: string, 'data', 'readonly', 'hidden', 'required', 'longtext'
    - data types: string, 'str', 'int', 'float', 'bool', 'set', 'list', 'dict', 'DataJson', 'Enum'
    
    :value: a dict for fk_map and a set of string for other types.

    *example*::
    ```python
        key_info = { 
            'data': ( 'entity_id', 'entity_name', 'old_entity_id' ),
            'readonly': { 'entity_id' },
            'hidden': { 'entity_id', 'old_entity_id' }
        }
    ```
    """
    rel_info: dict[str, dict[str, type[Base] | str | tuple[Any, ...]]] = NotImplemented
    """
    A dict of relationship information for the class.

    .. example::
    ```python
        rel_info = {
            'entity': {
                'local_col': 'entity_id',
                'ref_table': 'entity', # must be single pk table
                'select_order': ('entity_name',)
            }
        }
    ```
    """
    def __init__(self, data: str | dict | None = None, **kwargs: Any) -> None:
        """
        :param data: string or dict or none, json string or dict to be converted to DataJson object.
        :param kwargs: other keyword arguments which override the correspondent entries in parameter `data`.
        """
        data_dict = self.load(data, **kwargs)
        self.__dict__.update(data_dict)

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Main purpose of this method is to initialize key_info and rel_info 
        of the sub class as an empty dict to avoid errors.

        :param kwargs: kwargs are not used in this method but in superclass method.
        """
        super().__init_subclass__(**kwargs)
        if cls.key_info is NotImplemented:
            cls.key_info = dict()
        if cls.rel_info is NotImplemented:
            cls.rel_info = dict()

    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs: Any) -> dict[str, Any]:
        """
        :return: a dictionary containing valid data for this class
        :param data: string or dict or none, json string or dict to be converted to DataJson object.
        :param kwargs: other keyword arguments which override the correspondent entries in parameter `data`.
        :raise AttributeError: if the data is not valid for this class.
        """
        from app.utils import args_to_dict
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
        :return: json string of the data dictionary.
        :raise AttributeError: if the data is not valid for this class.
        """
        return json.dumps(self.data_dict(serializeable=True))
    
    @classmethod
    def get_cls_from_dict(cls, data: dict[str, Any]) -> type['DataJson']:
        """
        If called by Base class, read the class id from `data`.
        Otherwise, return the class calling this method if the data is valid.

        :return: a class of DataJson.
        :param data: a dictionary containing data to be converted to DataJson object.
        :raise AttributeError: if the data is not valid for DataJson.
        """
        if cls.__datajson_id__ is NotImplemented:
            datajson_id = data.get('__datajson_id__', None)
            if datajson_id is None or not isinstance(datajson_id, str):
                raise AttributeError(f'Invalid datajson_id {datajson_id} in {data}')
            data_json_cls = cls.class_map.get(datajson_id, None)
            if data_json_cls is None:
                raise AttributeError(f'Invalid {datajson_id} in class_map {cls.class_map}')
        else:
            data_json_cls = cls
        
        required_keys = data_json_cls.get_keys('required')
        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise AttributeError(f'Missing required keys: {missing_keys} in {data}')
        
        readonly_keys = data_json_cls.get_keys('readonly')
        if (readonly_keys - (readonly_keys - data.keys())):
            raise AttributeError(f'Readonly keys: {readonly_keys} in {data}')
        return data_json_cls

    @classmethod
    def _load_dict(cls, data: dict) -> dict[str, Any]:   
        """
        convert the `data` into a valid data dictionary for the class.
        .. attention::
        - only modifiable entries are converted.
        - readonly entries are ignored.

        :param data: a dictionary containing data to be converted to DataJson object.
        :return: a dictionary containing valid data for this class.
        :raise AttributeError: if the data is not valid for this class.
        """
        data_json_cls = cls
        if cls.__datajson_id__ == NotImplemented:
            data_json_cls = cls.get_cls_from_dict(data)
        data_dict = {}
        data_dict['__datajson_id__'] = data_json_cls.__datajson_id__
        mod_keys = data_json_cls.get_keys('modifiable')

        for key in mod_keys:
            value = data.get(key, None)
            data_dict[key] = data_json_cls.convert_value_by_attr_type(value, key) # type: ignore
        return data_dict

    @classmethod
    def convert_value_by_attr_type(cls, value: Any, attr_key: str) -> Any:
        """
        convert the value to the type of the attribute if the class.

        :param value: the value to be converted.
        :param attr_key: the key of the attribute.
        :raise AttributeError: if the attribute is not found in the class.
        """
        if value is None or value == '':
            return None
        attr = getattr(cls, attr_key, None)
        if attr is None:
            raise AttributeError(f'Attribute {attr_key} not found in {cls}')
        attr_type = type(attr)
        converted_value = convert_value_by_python_type(value, attr_type)    
        return converted_value
      
    def data_dict(self, serializeable: bool = False) -> dict[str, Any]:
        """
        :return: a dictionary containing the data of the object.
        :param serializeable: If True, serialize the values in the dictionary.
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
    def get_col_rel_map(cls) -> dict[str, str]:
        """
        :return: a dict of the relationship map for the class.
        """
        rel_info = cls.rel_info
        col_rel_map = dict()
        if rel_info:
            for r_k, r_i in rel_info.items():
                if not isinstance(r_i, dict):
                    raise AttributeError(f'Invalid foreignkeys {r_i} for {cls}')
                local_col_key = r_i.get('local_col', None)
                if local_col_key is None:
                    raise AttributeError(f'Invalid local_col {local_col_key} for {cls}')
                col_rel_map[local_col_key] = r_k    
        return col_rel_map
    
    @classmethod
    def get_obj(cls, data: str | dict, **kwargs: Any) -> Optional['DataJson']:
        """
        :return: DataJson object or None
        :param data: string or dict of the initial data
        :param **kwargs: keyword arguments that will override the entry with same key in the data
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
        Retrieve a set of keys based on the specified type information.

        The allowed type information strings are:
          - Data types: "date", "json", "int", "float", "bool", "set", "list", "dict", "str", "DataJson", "Enum"
          - User-defined types in key_info: "readonly", "hidden", "required", "data", "longtext"
          - Calculated types: "modifiable", "visible"

        :param args: One or more type information strings indicating which keys to retrieve.
                     For example, passing "data" will return all keys defined as data fields.
        :return: A set of keys (as strings) corresponding to the specified type information.
        :raises AttributeError: If an invalid type information string is provided or if a key cannot be found.
        """
        keys = set()
        for info in args:
            # Return cached info if available
            if info in cls.key_info:
                info_keys = cls.key_info.get(info, set())
                if info == 'data':
                    info_keys = set(info_keys)
                keys.update(info_keys)
            elif info == 'single_rel':
                return set(cls.rel_info.keys())
            elif info == 'modifiable':
                info_keys = cls.get_keys('data') - cls.get_keys('readonly')
                cls.key_info[info] = info_keys  # cache the result
                keys.update(info_keys)
            elif info == 'visible':
                info_keys = cls.get_keys('data') - cls.get_keys('hidden')
                cls.key_info[info] = info_keys  # cache the result
                keys.update(info_keys)
            elif info in {'date', 'json', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_keys = set()
                for data_key in cls.get_keys('data') - cls.get_keys('single_rel'):
                    attr = getattr(cls, data_key, None)  # type: ignore
                    if attr is None:
                        raise AttributeError(f'Attribute {data_key} not found in {cls}')
                    if isinstance(attr, eval(info)):
                        info_keys.add(data_key)
                cls.key_info[info] = info_keys  # cache the result
                keys.update(info_keys)
        return keys

    @classmethod
    def get_headers(cls) -> list[str]:
        """
        :return: a list of visible keys in the model.
        """
        cache = cls.key_info.get('headers', list())
        if not cache:
            cache = cls.key_info['headers'] = [key for key in cls.key_info.get('data') if key not in cls.get_keys('hidden')] # type: ignore
        return cache # type: ignore

    @abstractmethod
    def validate(self, *args, **kwargs) -> bool:
        pass
