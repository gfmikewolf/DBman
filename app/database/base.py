# app/database/base.py

__all__ = ['Base', 'DataJson', 'DataJsonType']

# python
from sqlite3 import DatabaseError
from typing import Any, Iterable, Optional
from enum import Enum, auto 
from datetime import date
import json

# sqlalchemy
from sqlalchemy import Column, select, Select
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import DeclarativeBase, Session, ColumnProperty

# app
from app.utils.common import args_to_dict

def serialize_value(attr: Any) -> Any:
    """
    convert the `attr` to a serializable value according to its data type.
    """
    
    if isinstance(attr, ColumnProperty):
        attr_type = attr.type.python_type
    else:
        attr_type = type(attr)
    srl_value = None
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

    if value is None or (value == '' and not issubclass(python_type, str)):
        return None
    converted_value = value
    if isinstance(value, python_type):
        return value
    elif issubclass(python_type, date) and isinstance(value, str):
        converted_value = date.fromisoformat(value) if value else None
    elif issubclass(python_type, int) and isinstance(value, str):
        converted_value = python_type(value)
    elif issubclass(python_type, float) and (isinstance(value, str) or isinstance(value, int)):
        converted_value = python_type(value)
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
    elif issubclass(python_type, Enum) and (isinstance(value, str) or isinstance(value, int)):
        if isinstance(value, str):
            value = value.lower()
        converted_value = python_type(value)
    else:
        raise AttributeError(f'Value {value} ({type(value).__name__}) of wrong format for key: ({python_type.__name__})')
    return converted_value

class Base(DeclarativeBase):
    """
    Base class for all database models in the application.

    .. attention:: 
        - `model_map` shall be set before using the class and its subclasses.
        - `db_session` shall be initialized before using *fetch_* methods.

    :cvar model_map: { database table name: Class name of the model }
    :cvar db_session: SQLAlchemy Session object.
    :cvar col_key_info: Dictionary and cache of column information valued by keys.
    :cvar col_info: Dictionary and cache of column information valued by columns.
    """
    model_map: dict[str, type['Base']] = {}
    """
    a dictionary of model classes, used to identify the class from the __tablename__ key in the data dictionary.

    .. attention:: must be defined in the subclass before using its properties or methods.
    """
    
    db_session: Session | None = None
    """
    SQLAlchemy `Session`. 
    
    .. attention:: Must be set to a valid session before using certain methods of the class.
    """

    col_key_info: dict[str, Any] = NotImplemented
    """
    Information about the columns in the database table.

    :key: 
    string, information type, including:
        - user-defined types: string, *readonly*, *hidden*, *required*, *rel_map*
        - data types: string, *str*, *int*, *float*, *bool*, *set*, *list*, *dict*, *DataJson*, *Enum*
    
    :value: 
    a set of string for user-defined types and a dict for data types, or
    a dict for relationship map type `ref_map`, including the entries below:
        - `ref_map['ref_name_col']`: referenced name column name, e.g. *contract_name*
        - `ref_map['select_order']`: order by tuple of column name and order direction (asc or desc)

    .. attention:: - must be defined in the subclass before using its properties or methods.
                   - the return type of set of string has no order.
    """
    
    col_info: dict[str, set[Column]] = NotImplemented
    """
    Information about the columns in the database table. See `col_key_info` for details.
    
    :rtypes: dict[str, set[Column]]
    """
    
    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Initialize the class variables such as col_info and col_key_info.

        .. attention::  `col_key_info` and `col_info` are not implemented in the base class
                        but initialized in this method 
                        to create independent subclass level variables.
        """
        super().__init_subclass__(**kwargs)
        if cls.col_key_info is NotImplemented:
            cls.col_key_info = dict()
        if cls.col_info is NotImplemented:
            cls.col_info = dict()

    def replace_data(self, data: str | dict | None = None, **kwargs: Any) -> None:
        """
        replace the data of an instance with `data` and `kwargs`.

        :param data: string or dict or none, json string or dict to be converted to DataJson object.
        :param kwargs: other keyword arguments which override the correspondent entries in parameter `data`.
        """
        args_dict = args_to_dict(data, **kwargs)
        if self.get_cls_from_dict(args_dict) is None:
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {self}')
        mod_col_keys = self.get_col_keys('modifiable')
        if args_dict.keys() - mod_col_keys: # check if there is any keys not modifiable
            raise AttributeError(f'Invalid data: {args_dict} to match {self}')
        for key in mod_col_keys:
            if key in args_dict:
                value = args_dict[key]
                if value is not None:
                    if key in self.get_col_keys('DataJson'):
                        value = DataJson.get_obj(value)
                    setattr(self, key, value)
    
    @classmethod
    def get_headers(cls) -> list[str]:
        """
        :return: a tuple of column keys in the database table 
        if the column is not an invisible primary key.
        """
        return  [
            col.key for col in cls.__mapper__.columns
            if col not in (cls.get_cols('pk') - cls.get_cols('visible'))
        ]


    @classmethod
    def get_cols(cls, *args: str) -> set[Column]:
        """
        :return: a set of columns in the database table with the specified information.
        :param args: a list of information strings, including:

            - user-defined types: string, 'readonly', 'hidden', 'required', 'rel_map'
            - data types: string, 'str', 'int', 'float', 'bool', 'set', 'list', 'dict', 'DataJson', 'Enum'
            - other args: return the columns with column.info[arg] exists
        :raise AttributeError: if the information is not valid for this class.

        .. notes:: the information is cached after the first fectch.
        """
        cols = set()
        for info in args:
            if info in cls.col_info:
                cols.update(cls.col_info[info])
            elif info in {'readonly', 'hidden', 'longtext'}:
                info_keys = cls.col_key_info.get(info, set())
                if info_keys:
                    info_cols = {cls.__mapper__.columns[key] for key in info_keys}
                    cls.col_info[info] = info_cols
                    cols.update(info_cols)
            elif info == 'required':
                info_cols = set()
                for col in cls.__mapper__.columns:
                    # If the column is not nullable and not autoincrement, it is required.
                    if (not col.nullable) and (col.autoincrement is not True):
                        info_cols.add(col)
                cls.col_key_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'data':
                info_cols = set(cls.__mapper__.columns)
                if hasattr(cls, '_name'):
                    info_cols.add(cls._name) # type: ignore
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'pk':
                info_cols = set(cls.__mapper__.primary_key)
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'modifiable':
                info_cols = cls.get_cols('data') - cls.get_cols('readonly')
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'visible':
                info_cols = cls.get_cols('data') - cls.get_cols('hidden')
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info in {'date', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_cols = set()
                for col in cls.get_cols('data'):
                    if issubclass(col.type.python_type, eval(info)):
                        info_cols.add(col)
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'fk':
                info_cols = set()
                for col in cls.get_cols('data'):
                    if col.foreign_keys:
                        info_cols.add(col)
                cls.col_info[info] = info_cols 
                cols.update(info_cols)   
            else:
                info_cols = set()
                for col in cls.__mapper__.columns:
                    if col.info.get(info, None) is not None:
                        info_cols.add(col)
                cols.update(info_cols)
        return cols
    
    @classmethod
    def get_col_keys(cls, *args: str) -> set[str]:
        """
        :return: a set keys of `get_cols(args)`. 
        :param args: a list of information strings, including:

            - user-defined types: string, 'readonly', 'hidden', 'required', 'rel_map'
            - data types: string, 'str', 'int', 'float', 'bool', 'set', 'list', 'dict', 'DataJson', 'Enum'
            - other args: return the columns with column.info[arg] exists
        :raise AttributeError: if the information is not valid for this class.

        .. notes:: the information is cached after the first fectch.
        """
        col_keys = set()
        for info in args:
            info_keys = cls.col_key_info.get(info, set())
            if not info_keys:
                info_keys = {col.key for col in cls.get_cols(info)}
                cls.col_key_info[info] = info_keys  
            col_keys.update(info_keys)
        return col_keys
    
    @classmethod
    def get_cls_from_dict(cls, data : dict[str, Any]) -> type['Base'] | None:
        """
        Check the key validity in the data and
        return the Base class that match the data if valid.

        :return: the Base class from the data dictionary.
        """
        if cls.__tablename__ is None:
            tablename = data.get('__tablename__', None)
            model_cls = cls.model_map.get(tablename, None)
            if model_cls is None:
                raise AttributeError(f'Invalid {tablename} in class_map {cls.model_map}')
        else:
            tablename = cls.__tablename__
            model_cls = cls
        
        required_keys = model_cls.get_col_keys('required')
        # find keys that exist in required_keys but not in data
        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise AttributeError(f'Missing required keys: {missing_keys} in {data}')
        
        # raise error if data has readonly keys
        readonly_keys = model_cls.get_col_keys('readonly')
        if (readonly_keys - (readonly_keys - data.keys())):
            raise AttributeError(f'Readonly keys: {readonly_keys} in {data}')
        return model_cls
    
    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
        """
        convert json string or dict with keywords entries to a valid dict of the class.

        .. attention:: `kwargs` will override data entries with the same keys.
        """
        args_dict = args_to_dict(data, **kwargs)
        model_cls = cls.get_cls_from_dict(args_dict)
        if model_cls is None:
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {cls}')

        if not args_dict:
            return args_dict
        else:
            return model_cls._load_dict(args_dict)
          
    @classmethod
    def _load_dict(cls, data: dict) -> dict[str, Any]:   
        """
        :return: a dictionary containing valid data for this class 
        with data types converted according to the class attribute python types.

        :param data: a dictionary with valid key structure to be converted to the class object.
        
        .. attention::
        readonly keys in the data are neglected.
        """
        if cls.__tablename__ is None:
            model_cls = cls.get_cls_from_dict(data)
            if model_cls is None:
                raise AttributeError(f'Invalid data {data} for {cls}')
            tablename = model_cls.__tablename__
        else:
            tablename = cls.__tablename__
            model_cls = cls
                  
        mod_cols = model_cls.get_cols('modifiable')

        data_dict = {}
        data_dict['__tablename__'] = tablename
        
        for mod_col in mod_cols:
            value = data.get(mod_col.key, None)
            if value is not None:
                data_dict[mod_col.key] = convert_value_by_python_type(value, mod_col)
        return data_dict

    def __setattr__(self, key: str, value: Any) -> None:
        """
        set data attribute of the class with the datatypes converted accordingly.
        if the key is not in `cls.get_col_keys('data')`, it will be set as is.
        
        :raise AttributeError: if the key is not valid e.g. readonly for this class or 
        the value is not valid for the key.
        """
        converted_value = value
        if key in self.get_col_keys('data'):
            readonly_keys = self.get_col_keys('readonly')
            if key in readonly_keys:
                raise AttributeError(f'Key {key} is readonly for {self}')
            attr = getattr(self.__class__, key, None)
            if attr is None:
                raise AttributeError(f'Invalid key {key} for {self}')
            if hasattr(attr, 'type') and hasattr(attr.type, 'python_type'):
                converted_value = convert_value_by_python_type(value, attr.type.python_type)
        super().__setattr__(key, converted_value)
    
    def _super_setattr(self, key: str, value: Any) -> None:
        """
        orginal __setattr__ method reserved to modify readonly keys and etc.
        """
        super().__setattr__(key, value)
   
    def data_dict(self, serializeable: bool = False) -> dict[str, Any]:
        """
        :return: a dictionary containing data of the instance.
        :param serializeable: if True, the data is serialized to allowed types for JSON.
        """
        data_dict = {'__tablename__': self.__tablename__}
        data_keys = self.get_col_keys('data')
        for data_key in data_keys:
            if not hasattr(self, data_key):
                raise AttributeError(f'Invalid attribute {data_key} for {self}')
            attr = getattr(self, data_key)
            if attr is None:
                data_dict[data_key] = '' if serializeable else None
            else:
                data_dict[data_key] = serialize_value(attr) if serializeable else attr
        
        return data_dict
  
    @classmethod
    def _datatable_select_all(cls) -> tuple[Select, dict[str, tuple[str, str]]]:
        """
        :return: a select statement for all rows in the table, and a ref_map.
            
            - ref_map: keyed by relationship key, and the value is a tuple of
                (local column key, referenced table key).

        .. fields:: (id, name, `foreign_key_column.label(relationship.key)` [referenced name column], ...)
            - only visible columns are selected.
            - primary key columns are always selected.
            - foreign key columns are selected with the referenced name column of 
              the referenced table if it exists. 
            - The name column or the foreign key column (if name column does not exist)
              is labeled with the relationship key.
        
        """
        mapper = cls.__mapper__
        
        # attention: lack relationship names in visible keys
        visible_keys = cls.get_col_keys('visible') 
        # primary key columns need to be retrieved always for reference purpose

        joins = []
        ref_map = dict()
        # get ref_name_col in relationship info
        rel_map = cls.col_key_info.get('rel_map', dict())

        query_cols = []
        query_cols.extend(list(mapper.primary_key))
        for col in mapper.columns:
            if col.key in visible_keys:
                query_cols.append(col)
        for rel in mapper.relationships:
            if rel.uselist:
                continue
            ref_Model = rel.entity.class_
            local_col = next(iter(rel.local_columns))
            rel_info = rel_map.get(rel.key, dict()) # type: ignore
            if rel_info:
                name_col_name = rel_info.get('ref_name_col', '_name') # type: ignore
                ref_map[rel.key] = (local_col.key, ref_Model.__tablename__)
                if hasattr(ref_Model, name_col_name):
                    name_col = getattr(ref_Model, name_col_name)
                    query_cols.append(local_col)
                    query_cols.append(name_col.label(rel.key))
                    joins.append(ref_Model)                   
                else:
                    query_cols.append(local_col.label(rel.key))
        query = select(*query_cols)
        if joins:
            query = query.select_from(cls)
            for join_Model in joins:
                query = query.outerjoin(join_Model)
        return query, ref_map
    
    @classmethod
    def _convert_value_to_viewer(cls, key:str, value: Any) -> Any:
        """
        :return: convert the value to a viewable value in web page.

            - None is converted to empty string.
            - DataJson is converted to a JSON string.
            - other types are converted to string.
        """
        if value is None:
            value = ''
        if key in cls.get_col_keys('DataJson') and isinstance(value, DataJson):
            value = value.dumps()
        if key in cls.get_col_keys('Enum') and isinstance(value, Enum):
            value = value.name
        return str(value)
    
    @classmethod
    def fetch_datatable_dict(cls) -> dict[str, Any]:
        """
        :return: a dict of datatable for the class.
        
        *example*::
        ```python
            datatable = {
                'headers': ('id', 'name', 'contract_id', 'contract', ),
                'data': [
                    (1, 'entity1', 1, 'contract1'),
                    (2, 'entity2', 2, 'contract2'),
                ],
                '_pks': ['1', '2'],
                'ref_map': {
                    'contract': (index of 'contract_id', 'table_contract')
                }
            }
        ```
        """
        query, ref_map = cls._datatable_select_all()
        visible_keys = cls.get_col_keys('visible')
        pk_keys = cls.get_col_keys('pk')
        datatable = dict()
        
        try:
            result = cls.db_session.execute(query) # type: ignore
        except DatabaseError as e:
            raise DatabaseError(f'Invalid query {query} or session {cls.db_session} for {cls}')
        datatable['headers'] = [
            key for key in result.keys() 
            if key in visible_keys | ref_map.keys() 
        ]
        datatable['data'] = []
        datatable['_pks'] = []
        datatable['_ref_pks'] = []
        datatable['ref_map'] = ref_map
        
        if not result:
            return datatable  
        
        ref_pks = dict()
        for key in ref_map.keys():
            ref_pks[key] = list()
        json_keys = cls.get_col_keys('DataJson')
        visible_json_keys = json_keys - (json_keys - visible_keys)
        datatable['fields_datajson'] = visible_json_keys

        for row in result:
            datarow = []
            _pks = []
            for key in result.keys(): 
                value = row._mapping[key]
                if key in pk_keys:
                    _pks.append(str(value))
                for rel_key, ref_tuple in ref_map.items():
                    if key == ref_tuple[0]: # ref_tuple[0] is the local column key
                        ref_pks[rel_key].append(str(value))
                if key in visible_keys | ref_map.keys():
                    value = cls._convert_value_to_viewer(key, value)
                    datarow.append(value)
            datatable['data'].append(datarow)
            datatable['_pks'].append(','.join(_pks))
        datatable['_ref_pks'] = ref_pks
        return datatable
    
    @classmethod
    def fetch_ref_list(cls, col_name: str, order_by: tuple[str, ...] | None = None) -> list[tuple[str, str]]:
        """
        :return: list of tuple[referenced pk value joined by comma, referenced name column value]
        :param col_name: referenced name column name
        :param order_by: order by tuple of column name and order direction (asc or desc)
        """
        
        list_pks_name = []
        pks = cls.__mapper__.primary_key
        if not hasattr(cls, col_name):
            return list_pks_name
        col = getattr(cls, col_name)
        query = select(*pks, col)
        if order_by is not None and isinstance(order_by, Iterable):
            for rno_str in order_by:   
                rno_strs = rno_str.split('.')
                if hasattr(cls, rno_strs[0]):
                    len_rno = len(rno_strs)
                    if len_rno == 1 or (len_rno == 2 and rno_strs[1].lower() == 'asc'):
                        query = query.order_by(getattr(cls, rno_strs[0]))
                    elif len_rno == 2 and rno_strs[1].lower() == 'desc':
                        query = query.order_by(getattr(cls, rno_strs[0]).desc())
        if query is not None and Base.db_session is not None:
            try:
                result = Base.db_session.execute(query)
            except DatabaseError as e:
                raise DatabaseError(f'Invalid query {query}'
                    f'or session {cls.db_session}') 
                            
            for row in result:
                pk_values = ','.join(map(str, row[:-1]))
                name_value = row[-1]
                row_pks_name = (pk_values, name_value)
                list_pks_name.append(row_pks_name)
        return list_pks_name
    
    @classmethod
    def fetch_select_options(cls) -> dict[str, tuple[Any]]:
        """
        :return: a dict of select options for each relationship and enum type column

            - key: local column name 
            - value: [tuple[referenced pk value, referenced column value]]. Values are ordered according to col_key_info['rel_map'][local_col]['select_order']*
        
        *example*::
            orderby = { 'entity_name': tuple['entity_id', 'entity_frequency.desc'] }
        """
        
        select_options = dict()
        # Extract foreign key col and referenced pks and name tuple for each relationship
        mapper = cls.__mapper__
        for rel in mapper.relationships:
            list_pks_name = []
            if rel.uselist:
                continue
            ref_Model = rel.entity.class_
            local_col_key = next(iter(rel.local_columns)).key
            rel_map = cls.col_key_info.get('rel_map', {})
            rel_info = rel_map.get(rel.key, None) # type: ignore
            order_by = None
            order_by = rel_info.get('select_order', None) # type: ignore
            ref_name_col = rel_info.get('ref_name_col', '_name') # type: ignore
            list_pks_name = ref_Model.fetch_ref_list(ref_name_col, order_by=order_by) 
            select_options[local_col_key] = list_pks_name
        
        # Extract Enum types and get options from Enum definition
        enum_cols = cls.get_cols('Enum')
        for col in enum_cols:
            enum_cls = col.type.python_type
            if not issubclass(enum_cls, Enum):
                raise AttributeError(f'Invalid enum_cls {enum_cls} for {cls}')
            values = [(member.value, member.name) for member in enum_cls]
            select_options[col.key] = values        
        return select_options

    def fetch_rel_data(self, with_data: bool=False, with_lists: bool=False) -> dict[str, Any]:
        """
        :return: a dictionary containing the relationship data of the instance.
        :param with_data: if True, the data of the referenced objects are included.
        :param with_lists: if True, the data of the referenced lists are included.

        *example*::
        ```python
            rel_data = {
                'ref_names': {
                    'entity_id': {
                        'field_name': 'entity_id',
                        'tablename': 'table_entity',
                        'ref_name': 'entity1',
                        'headers': ('id', 'name', ...),
                        'data_dict': {'id': 1, 'name': 'entity1', ...},
                        'ref_names': {...}
                    },
                    ...
                },
                'ref_lists': {
                    'contract': (
                        [
                            {'id': 1, ...},
                            {'id': 2, ...},
                            ...
                        ],
                        data_struct = {
                            'tablename': 'table_contract',
                            'name_col': 'contract_name',
                            'pk_list': ('id',),
                            'headers': ('id', entity_id, ...)
                        },
                        ref_names = {
                            'entity_id': {
                                'field_name': 'entity_id',
                                'tablename': 'table_entity',
                                'ref_name': 'entity1',
                                'headers': ('id', 'name', ...),
                                'data_dict': {'id': 1, 'name': 'entity1', ...},
                                'ref_names': {...}
                            },
                        }
                    ),
                    ...
                },
                'datajson_ref_names': {
                    ...
                }
            }
        ```
        """
        # list objects in self.relationships
        rel_data = dict()
        rel_data['ref_names'] = dict()
        rel_data['ref_lists'] = dict()
        rel_data['datajson_ref_names'] = dict()

        for rel in self.__mapper__.relationships:   
            local_col_key = next(iter(rel.local_columns)).key
            # get the referenced object(s)
            rel_obj = getattr(self, rel.key)
            # manytoone or manytomany relationship
            if rel.uselist:
                if not with_lists:
                    continue
                if len(rel_obj) == 0: # no object in the list
                    continue
                sample_obj = rel_obj[0] # all objects share the same class type
                sample_Model = sample_obj.__class__
                sample_mapper = sample_Model.__mapper__

                # data structure dict
                data_struct = dict()
                data_struct['ref_table'] = sample_Model.__tablename__
                data_struct['pk_list'] = [
                    col.key for col in sample_mapper.primary_key
                ]
                data_struct['datajson_ref_names'] = dict()
                # get rel_data from Datajson classes
                for datajson_key in self.get_col_keys('DataJson'):
                    datajson_obj = getattr(self, datajson_key)
                    data_struct['datajson_ref_names'][datajson_key] = datajson_obj.fetch_ref_names()

                name_col = getattr(sample_Model, '_name', None)
                if name_col:
                    # name_col can be of synonym or hybrid property type
                    # if name_col is a synonym property, get the name of the mapped column
                    # if name_col is a hybrid property, use ref_Model.name in the query
                    data_struct['name_col'] = getattr(name_col, '_name', '_name')
                # if name_col is false value, need to handle it by other methods

                data_struct['headers'] = sample_Model.get_headers()
                ref_names = sample_obj.fetch_rel_data(
                    with_data=False, with_lists=False)['ref_names']
                ref_list = dict()
                ref_list['data_struct'] = data_struct
                ref_list['ref_names'] = ref_names
                ref_list['data_list'] = [obj.data_dict(serializeable=True) for obj in rel_obj]

                rel_data['ref_lists'][rel.key] = ref_list
            
            # onetoone or manytoone relationship
            else:
                if rel_obj is None:
                    continue
                ref_Model = rel.entity.class_
                rel_map = self.col_key_info.get('rel_map', dict())
                ref_col_name = '_name'
                # RelationshipProperty has provided PK, FK and referenced table info
                # rel_map of Base usually provides ref_name_col and select_order
                # which is optional but in most cases ref_name_col is defined
                if isinstance(rel_map, dict) and rel.key in rel_map.keys():
                    rel_info = rel_map.get(rel.key)
                    if rel_info and isinstance(rel_info, dict):
                        # if ref_name_col is omitted, use '_name' to 
                        # get the name column of the referenced table
                        # name column is usually a synonym property
                        ref_col_name = rel_info.get('ref_name_col', '_name') 
                # find the name column value, else use the primary key value as
                # the reference value `ref_col_value`
                if isinstance(ref_col_name, str) and hasattr(ref_Model, ref_col_name):
                    ref_col_value = getattr(rel_obj, ref_col_name)
                else:
                    pk = rel_obj.__mapper__.primary_key[0]
                    ref_col_value = f'# {getattr(rel_obj, pk.key)}'
                
                ref_data = dict()
                ref_data['rel_key'] = rel.key             
                ref_data['ref_table'] = ref_Model.__tablename__
                ref_data['ref_name'] = ref_col_value
                if with_data:
                    ref_data['headers'] = rel_obj.get_headers()
                    ref_data['data_dict'] = rel_obj.data_dict(serializeable=True)
                    ref_rel_data = rel_obj.fetch_rel_data(
                        with_data=False, with_lists=False
                    )
                    ref_data['ref_names'] = ref_rel_data['ref_names']
                    ref_data['datajson_ref_names'] = ref_rel_data['datajson_ref_names']
                rel_data['ref_names'][local_col_key] = ref_data
        for key in self.get_col_keys('DataJson'):
            datajson_obj = getattr(self, key, None)
            if datajson_obj is None:
                continue
            if not isinstance(datajson_obj, DataJson):
                raise ValueError(f'attr {key} is not DataJson')
            rel_data['datajson_ref_names'][key] = datajson_obj.fetch_ref_names()
        return rel_data

    @classmethod
    def fetch_datajson_ref_map(cls) -> dict[str, str]:
        """
        :return: dict {local_col.key: datajson_id_col.key }
        """
        datajson_cols = cls.get_cols('DataJson')
        datajson_id_cols = cls.get_cols('DataJson_id_for')
        datajson_ref_map = dict()
        for dj_col in datajson_cols:
            found = False
            for id_col in datajson_id_cols:
                id = id_col.info.get('DataJson_id_for', None)
                if id and id == dj_col.key:
                    datajson_ref_map[dj_col.key] = id_col.key
                    found = True
            if found == False:
                raise AttributeError(f'{cls}.{dj_col.key} is a class derived from DataJson, but its identity col is not found in the same model')
        return datajson_ref_map
    
class DataJsonType(TypeDecorator):
    """
    DataJson type decorator for SQLAlchemy.
    """
    impl = JSON
    cache_ok = True

    @property
    def python_type(self):
        return DataJson

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.data_dict(serializeable=True)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return DataJson.get_obj(value)
        return value

class DataJson:
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

    attr_info: dict[str, Any] = NotImplemented
    """
    A dict of information regarding attributes of the class, including user-defined types and data types.

    .. attention::
    - Should be **defined in the subclass** before using its properties or methods.
    - **a set has no order.**
    
    :key: string, infomation type, including:
    - user-defined types: string, 'data', 'readonly', 'hidden', 'required', 'rel_map'
    - data types: string, 'str', 'int', 'float', 'bool', 'set', 'list', 'dict', 'DataJson', 'Enum'
    
    :value: a dict for fk_map and a set of string for other types.

    *example*::
    ```python
        attr_info = { 
            'data': { 'old_entity_id' },
            'rel_map': {
                'old_entity': {
                    'local_col': 'old_entity_id',
                    'ref_table': 'entity', # must be single pk table
                    'ref_name_col': 'entity_name', # if not exist, use relationship name
                    'select_order': ('entity_name',)
                }
            }
        }
    ```
    """
    def __init__(self, data: str | dict | None = None, **kwargs):
        """
        :param data: string or dict or none, json string or dict to be converted to DataJson object.
        :param kwargs: other keyword arguments which override the correspondent entries in parameter `data`.
        """
        data_dict = self.load(data, **kwargs)
        self.__dict__.update(data_dict)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Main purpose of this method is to initialize attr_info of the sub class as an empty dict to avoid errors.

        :param kwargs: kwargs are not used in this method but in superclass method.
        """
        super().__init_subclass__(**kwargs)
        if cls.attr_info is NotImplemented:
            cls.attr_info = dict()

    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
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
            if value is not None:
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

        attr = getattr(cls, attr_key, None)
        if attr is None:
            raise AttributeError(f'Attribute {attr_key} not found in {cls}')
        attr_type = type(attr)
        converted_value = convert_value_by_python_type(value, attr_type)    
        return converted_value
    
    def fetch_ref_names(self) -> dict[str, Any]:
        """
        Get the relationship data of the current object.
        
        .. attention::
        - Base.db_session must be active before calling this method.
        
        :return: A dictionary containing the relationship data.
        
        *example* ::
        ```python
            ref_names = {
                local_col_key : {
                    'rel_key': 'relationship key' 
                    'ref_table': 'referenced table name',
                    'ref_name': 'referenced name column value'
                }
            }
        },
        ```  
        """
        # list objects in self.relationships
        ref_names = dict()
        for rel_key, rel_info in self.attr_info.get('rel_map', dict()).items():  
            ref_table = rel_info.get('ref_table')
            ref_name_col_key = rel_info.get('name_col', '_name')
            local_col_key = rel_info.get('local_col')
            rel_info = dict()
            ref_Model = Base.model_map.get(ref_table)
            if ref_Model is None:
                raise AttributeError(f'Invalid tablename {ref_table} in attr_info for {self.__class__}')
            ref_name_col = getattr(ref_Model, ref_name_col_key, None)
            local_col_value = getattr(self, local_col_key)
            if not local_col_value: # skip false local FK values
                continue
            # fill ref_names with reference entries
            rel_info['headers'] = self.get_keys('data')
            rel_info['rel_key'] = rel_key
            rel_info['ref_table'] = ref_table
            
            if Base.db_session:
                ref_instance = Base.db_session.get(ref_Model, local_col_value)
                
                if ref_instance is None:
                    rel_info['ref_name'] = ''
                else:
                    if ref_name_col:
                        rel_info['ref_name'] = getattr(ref_instance, ref_name_col_key, None)
                    else:
                        pk = ref_Model.__mapper__.primary_key[0]
                        rel_info['ref_name'] = f'# {getattr(ref_instance, pk.key)}'

            if local_col_key and rel_info:
                ref_names[local_col_key] = rel_info
        return ref_names
    
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
          - User-defined types in attr_info: "readonly", "hidden", "required", "data", "longtext"
          - Calculated types: "modifiable", "visible"

        :param args: One or more type information strings indicating which keys to retrieve.
                     For example, passing "data" will return all keys defined as data fields.
        :return: A set of keys (as strings) corresponding to the specified type information.
        :raises AttributeError: If an invalid type information string is provided or if a key cannot be found.
        """
        keys = set()
        for info in args:
            # Return cached info if available
            if info in cls.attr_info:
                keys.update(cls.attr_info[info])
            elif info in {'readonly', 'hidden', 'required', 'data', 'longtext'}:
                info_keys = cls.attr_info.get(info, set())
                keys.update(info_keys)
            elif info == 'modifiable':
                info_keys = cls.get_keys('data') - cls.get_keys('readonly')
                cls.attr_info[info] = info_keys  # cache the result
                keys.update(info_keys)
            elif info == 'visible':
                info_keys = cls.get_keys('data') - cls.get_keys('hidden')
                cls.attr_info[info] = info_keys  # cache the result
                keys.update(info_keys)
            elif info in {'date', 'json', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_keys = set()
                for data_key in cls.get_keys('data'):
                    attr = getattr(cls, data_key, None)  # type: ignore
                    if attr is None:
                        raise AttributeError(f'Attribute {data_key} not found in {cls}')
                    if isinstance(attr, eval(info)):
                        info_keys.add(data_key)
                cls.attr_info[info] = info_keys  # cache the result
                keys.update(info_keys)
            else:
                raise AttributeError(f'Invalid key info {info} for {cls}')
        return keys

    @classmethod
    def fetch_select_options(cls) -> dict[str, list[tuple[str, str]]]:
        """
        :return: dict of select options of the Model.
        - keys: local column name
        - values: a list of tuples comprised of 2 elements
            - element[0]: referenced pk value
            - element[1]: referenced name column value
            - the list is ordered according to the col_key_info['ref_name_order']
        
        .. requirements::
            Base.db_session must be an active session() before calling this method.
        """
        options = dict()
        if cls.__datajson_id__ == NotImplemented:
            raise AttributeError('Cannot call fetch_select_options() on DataJson.')
        rel_map = cls.attr_info.get('rel_map', dict())
        cached = dict()
        for rel, rel_info in rel_map.items():
            if not isinstance(rel_info, dict):
                raise AttributeError(f'Invalid foreignkeys {rel_info} for {cls}')
            tablename = rel_info.get('ref_table', None)
            if tablename is None:
                raise AttributeError(f'Invalid ref_table {tablename} for {cls}')
            local_col_key = rel_info.get('local_col', None)
            if local_col_key is None:
                raise AttributeError(f'Invalid local_col {local_col_key} for {cls}')
            
            ref_Model = Base.model_map[tablename]
            if ref_Model is None:
                raise AttributeError(f'Invalid Model {ref_Model} for {cls}')
            
            ref_name_col_name = rel_info.get('name_col', None)
            ref_name_col = getattr(ref_Model, ref_name_col_name, None)
            if ref_name_col is None:
                raise AttributeError(f'Invalid ref_name_col {ref_name_col} for {cls}')
            
            if ref_name_col in cached.keys():
                options[local_col_key] = cached[ref_name_col]
            else:
                list_pks_name = ref_Model.fetch_ref_list(ref_name_col_name, rel_info.get('select_order', None))
                options[local_col_key] = list_pks_name
                cached[ref_name_col] = list_pks_name

        for enum_key in cls.get_keys('Enum'):
            enum_attr = getattr(cls, enum_key, None)
            if enum_attr is None:
                raise AttributeError(f'Attribute {enum_key} not found in {cls}')
            enum_cls = type(enum_attr)
            if not issubclass(enum_cls, Enum):
                raise AttributeError(f'Invalid Enum {enum_cls} for {cls}')
            options[enum_key] = [(member.value, member.name) for member in enum_cls]
        return options
    
    @classmethod
    def fetch_structure(cls) -> dict[str, Any]:
        """
        :return: dict of structure of the DataJson class
        - keys: data, required, readonly, date, Enum, foreign_keys, longtext
        - values: list of keys in the class
        """
        struct = dict()
        if cls == DataJson:
            raise AttributeError('Cannot call fetch_structure() on DataJson')
        
        struct['__datajson_id__'] = cls.__datajson_id__
        struct['data'] = [key for key in cls.__dict__ if key in cls.get_keys('data')]
        struct['required'] = cls.get_keys('required')
        struct['readonly'] = cls.get_keys('readonly')
        struct['date'] = cls.get_keys('date')
        struct['longtext'] = cls.get_keys('longtext')
        struct['constraints'] = cls.attr_info.get('constraints',dict())
        struct['select_options'] = cls.fetch_select_options()
        return struct
