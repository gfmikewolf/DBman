# app/database/base.py

__all__ = ['Base', 'DataJson']

# python
import inspect as python_inspect
from typing import Any, Optional
from datetime import date # in use eval('date')
from enum import Enum # in use eval('Enum')
import json
from abc import ABC, abstractmethod
import logging
logger = logging.getLogger(__name__)

# sqlalchemy
from sqlalchemy import delete, insert, inspect, update
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Session

# app
from app.utils.common import args_to_dict
from .utils import serialize_value, convert_value_by_python_type

class Cache:
    __abstract__ = True
    active = False
    cache_map: list[type['Cache']] = []

    @classmethod
    def update_cache(cls, db_session: Session, *args: Any, **kw: Any) -> bool:
        """
        Update the cache with the given arguments.
        :param db_session: The database session to use for the update.
        :param args: Additional arguments for the update.
        :param kw: Keyword arguments for the update.
        :return: True if the cache was updated successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses of Cache must implement update_cache.")
    @classmethod
    def init_cache(cls, db_session: Session) -> None:
        """
        Initialize the cache with the given database session.
        :param db_session: The database session to use for the initialization.
        :return: True if the cache was initialized successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses of Cache must implement init_cache.")
    @classmethod
    def update_all(cls, db_session: Session, *args: Any, **kw: Any) -> bool:
        """
        Update cache for all subclasses of Cache.
        :param db_session: The database session to use for the update.
        :param args: Additional arguments for the update.
        :param kw: Keyword arguments for the update.
        """
        flag = True
        for model in cls.cache_map:
            if issubclass(model, Cache):
                success = model.update_cache(db_session, *args, **kw)
                if not success:
                    logger.error(f"Failed to update cache for {model.__name__}")
                flag = flag and success
        return flag
    
    @classmethod
    def init_caches(cls, db_session: Session) -> None:
        """
        Initialize the cache for all subclasses of Cache.
        """
        for model in cls.cache_map:
            if issubclass(model, Cache) and hasattr(model, 'init_cache'):
                if model.init_cache(db_session):
                    logger.info(f"Cache initialized for {model.__name__}")
                else:
                    logger.error(f"Failed to initialize cache for {model.__name__}")
        Cache.active = True
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
    data_list: list[str] = NotImplemented
    """
    A list of data keys in the model to be shown in the table.
    .. attention:: must be defined in the subclass before using its properties or methods.
    """
    key_info: dict[str, set[str]] = NotImplemented
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

    func_map: dict[str, Any] = {}
    """
    A dictionary of functions that can be called from the database.

    .. example::
    ```python
        func_map = {
            'func_name': {
                'func': function,
                'input_types': (('file','ADCB_account_statement'),)
                'param_types': (str),
                # 'return_types': str assume all returns are string
            }
        }
    ```
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

    @classmethod
    def convert_value_by_data_type(cls, key: str, value: Any) -> Any:
        if key not in cls.get_keys('modifiable'):
            raise AttributeError(f'Key {key} is not modifiable for {cls}')
        attr = getattr(cls, key)
        try:
            attr_type = attr.type.python_type # assume all modifiable attributes are of type ColumnProperty
        except:
            return value
        return convert_value_by_python_type(value, attr_type)
    
    def update_data(self, data: str | dict | None = None, **kwargs: Any) -> None:
        """
        Update the data of an instance with `data` and `kwargs`.
        if the instance is new, entries not specified will be filled with default values.
        if the instance exists in database, only entries in parameters will be updated.
        .. attention:: This method will use active session to update the instance including creating new instance in case of polymorphic class.

        :param data: string or dict or none, json string or dict to be converted to DataJson object.
        :param kwargs: other keyword arguments which override the correspondent entries in parameter `data`.
        """
        args_dict = args_to_dict(data, **kwargs)
        old_cls = self.__class__
        i_old_cls = inspect(old_cls)
        if i_old_cls.polymorphic_identity is not None: # either base or sub class of a polymorphic class
            poly_base_cls = old_cls
            poly_on = i_old_cls.polymorphic_on
            poly_base_cls = i_old_cls.base_mapper.class_
            if poly_base_cls is None or inspect(poly_base_cls).polymorphic_on is None:
                poly_base_cls = old_cls
            
            poly_key = poly_on.name # type: ignore
            new_poly_name = args_dict.get(poly_key)
            old_poly_id = getattr(self, poly_key)
            new_poly_id = type(old_poly_id)[new_poly_name] # type: ignore assume poly identity is always Enum type
            if new_poly_id != old_poly_id:
                pk_cols = i_old_cls.primary_key
                pk_values = i_old_cls.primary_key_from_instance(self)
                pk_keys = [pk_col.key for pk_col in pk_cols]
                new_cls_item = i_old_cls.polymorphic_map.get(new_poly_id, None)
                if new_cls_item is None:
                    raise ValueError(f'{new_poly_id} not in {old_cls} polymorphic_map')
                new_cls = new_cls_item.class_
                i_self = inspect(self)
                sess = i_self.session
                if sess is None:
                    raise ValueError(f'Instance {self} not in session')
                if new_cls is None:
                    raise ValueError(f'{new_poly_id} not in {old_cls} polymorphic_map')
                if old_cls != poly_base_cls: # old class is base and new is sub
                    from sqlalchemy import select
                    old_table = old_cls.__table__
                    conditions = [
                        old_table.columns[pk_key]==pk_value 
                        for pk_key, pk_value in zip(pk_keys, pk_values)
                    ]
                    sess.execute(delete(old_cls.__table__).where(*conditions)) # type: ignore
                base_update_dict = dict()
                new_update_dict = dict()
                for key in args_dict:
                    if key in poly_base_cls.get_keys('modifiable'):
                        base_update_dict[key] = poly_base_cls.convert_value_by_data_type(key, args_dict[key])
                    elif key in new_cls.get_keys('modifiable'):
                        new_update_dict[key] = new_cls.convert_value_by_data_type(key, args_dict[key])
                pk_conditions = [
                    poly_base_cls.__table__.columns[pk_col.key]==pk_value 
                    for pk_col, pk_value in zip(pk_cols, pk_values)]
                sess.execute(update(poly_base_cls).values(**base_update_dict).where(*pk_conditions))
                # insert new sub-class data
                if new_cls != poly_base_cls:
                    for key, value in zip(pk_keys, pk_values):
                        new_update_dict[key] = value
                    sess.execute(insert(new_cls).values(**new_update_dict))
                return
        for key, value in args_dict.items():
            if key in self.get_keys('modifiable'):
                setattr(self, key, old_cls.convert_value_by_data_type(key, value))

    @classmethod
    def get_headers(cls) -> list[str]:
        """
        :return: a list of visible keys in the model.
        """
        cache = cls.key_info.get('headers', list())
        if not cache:
            cache = cls.key_info['headers'] = [ # type: ignore
                key for key in cls.data_list 
                if key not in cls.get_keys('hidden')
            ] 
        return cache # type: ignore

    @classmethod
    def get_polymorphic_base(cls) -> Optional[type['Base']]:
        """
        :return: the base class of the polymorphic class. None if not polymorphic.
        """
        insp = inspect(cls)
        if insp.polymorphic_identity is None:
            return None
        base_mapper = insp.base_mapper
        base_cls = base_mapper.class_
        if base_cls is None or base_mapper.polymorphic_on is None:
            return cls
        else:
            return base_cls

    @classmethod
    def get_polymorphic_key(cls) -> str: # type: ignore
        """
        :return: the key of the polymorphic class. Empty string if not polymorphic.
        """
        if inspect(cls).polymorphic_identity is not None:
            return inspect(cls).polymorphic_on.name # type: ignore
        return ''
    
    @classmethod
    def get_col_rel_map(cls) -> dict[str, str]:
        """
        :return: a dict of the single relationship map for the class.

        .. example::
        ```python
            { 'entity_id': 'entity', 'old_entity_id': 'old_entity' }
        ```
        """
        crm = dict()
        base_data_keys = set()

        for r in cls.__mapper__.relationships:
            local_col = next(iter(r.local_columns))
            local_col_key = local_col.key
            cond = (not r.uselist) and (r.secondary is None) and (local_col.foreign_keys)
            if cond and local_col_key:
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
            if info == 'data':
                keys.update(cls.data_list)
            elif info in cls.key_info:
                info_keys = cls.key_info.get(info, set())
                keys.update(info_keys)
            elif info == 'polybase_data':
                info_keys = set()
                p_base = cls.get_polymorphic_base()
                if p_base:
                    info_keys.update(p_base.data_list)
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
                info_keys = set(cls.data_list) - cls.get_keys('readonly')
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info == 'visible':
                info_keys = set(cls.data_list) - cls.get_keys('hidden')
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info in {'date', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'tuple' 'DataJson', 'Enum'}:
                info_keys = set()
                for key in set(cls.data_list) - cls.get_keys('single_rel'):
                    attr = python_inspect.getattr_static(cls, key)
                    if isinstance(attr, eval(info)):
                        info_keys.add(key)
                    elif isinstance(attr, hybrid_property):
                        fg = getattr(attr, 'fget', None)
                        if fg:
                            info_dict = getattr(fg, 'info', {})
                            if info_dict.get('type') == info:
                                info_keys.add(key)
                    else:
                        attr_type = getattr(attr, 'type', None)
                        if attr_type is not None:
                            python_type = getattr(attr_type, 'python_type', None)
                            if python_type and issubclass(python_type, eval(info)):
                                info_keys.add(key)
                cls.key_info[info] = info_keys
                keys.update(info_keys)
            elif info in {'single_rel', 'multi_rel'}:
                info_keys = set()
                for rel in cls.__mapper__.relationships:
                    if rel.key in cls.data_list:
                        if rel.uselist and info == 'multi_rel' :
                            info_keys.add(rel.key)
                        elif not rel.uselist and info == 'single_rel':
                            info_keys.add(rel.key)
                cls.key_info[info] = info_keys 
                keys.update(info_keys)   
            else:
                info_keys = set()
                for key in cls.data_list:
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
            raise ValueError(f'{table_name} not in Base.model_map')
        insp = inspect(data_cls)
        id_on = insp.polymorphic_on
        if id_on is not None: # Polymorphic class
            id_key = id_on.name
            attr_type = getattr(data_cls, id_key).type.python_type
            if issubclass(attr_type, Enum): # Enum type data from web form is string, need to convert to Enum
                id_v = attr_type[data.get(id_key)] # type: ignore
            else:
                id_v = data.get(id_key)
            id_pm = insp.polymorphic_map.get(id_v, None)
            if id_pm is None:
                raise ValueError(f'{id_v} not in {data_cls} polymorphic_map')
            data_cls = id_pm.class_
        conv_data = data_cls.convert_dict_by_attr_type(data)
        return data_cls(**conv_data)
    
    @classmethod
    def convert_dict_by_attr_type(cls, data: dict[str, Any]) -> dict[str, Any]:
        conv_data = dict()
        for key, value in data.items():
            converted_value = value
            if key in cls.data_list:
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
        for data_key in self.__class__.__mapper__.columns.keys():
            value = getattr(self, data_key, None)
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
    data_list: list[str] = NotImplemented
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

        data_keys = self.data_list
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
                info_keys = set(cls.data_list) - cls.get_keys('readonly')
                cls.key_info[info] = info_keys  # cache the result
                keys.update(info_keys)
            elif info == 'visible':
                info_keys = set(cls.data_list) - cls.get_keys('hidden')
                cls.key_info[info] = info_keys  # cache the result
                keys.update(info_keys)
            elif info in {'date', 'json', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_keys = set()
                for data_key in set(cls.data_list) - cls.get_keys('single_rel'):
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
