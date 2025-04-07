# app/base/crud/utils.py
from datetime import date
from typing import Any
from enum import Enum
from flask import abort, url_for
from sqlalchemy import select, inspect, table
from sqlalchemy.orm import Session
from config import Config
from app.extensions import Base, DataJson
from app import _

dbman_dict_name_list = Config.DATABASE_NAMES.split(',')  # type: ignore

def fetch_instance(table_name: str, pks: str, db_session: Session) -> Base:
    """
    Fetch a model instance from the database based on the table name and pks (primary keys).
    If pks is '_new', a new instance of the model is created.

    :returns: A Base model derived from DeclarativeBase.
    :param table_name: The name of the table to fetch the model from.
    :param pks: The primary keys joined by comma. If pks is '_new', a new instance is created.
    :raises: 404 if the table name is not found or the model instance is not found.
    
    *example*:
    ```python
    model = fetch_instance('user', '1,2')
    model = fetch_instance('user', '_new')
    ```
    """
    if table_name not in Base.model_map or (pks is None or pks == ''):
        abort(404)
    Model = Base.model_map[table_name]
    if pks == '_new':
        model = Model()
    else:
        pk_value_tuple = tuple(pks.split(','))
        if not db_session:
            raise DatabaseError(f'db_session must be initialized')
        model = db_session.get(Model, pk_value_tuple)
    if model is None:
        abort(404)
    return model

def fetch_tabledata(Model: type[Base], db_session: Session) -> dict[str, Any]:
    """
    :return: a select statement for all rows in the table, and a ref_map.

    .. example::
    ```python
        table_dict = fetch_datatable(Model, db_session)
        table_dict['headers'] = ['header1', 'header2', ...]
        table_dict['pks'] = ['pk1', 'pk2', ...]
        table_dict['data'] = [
            ['value1', 'value2', ...],
            ['value3', 'value4', ...],
            ...
        ]
    ```
    """
    header_list = Model.get_headers()

    table_dict = dict()
    table_dict['headers'] = [
        _(header_key, dbman_dict_name_list) 
        for header_key in header_list
    ]
    table_dict['pks'] = list()
    table_dict['data'] = list()

    instances = db_session.scalars(select(Model)).all()
    for instance in instances:
        mapper = inspect(instance)
        table_dict['pks'].append(
            ','.join([str(pk) for pk in mapper.identity]) # type: ignore
        )
        table_dict['data'].append(
            [
                fetch_viewable_value(instance, header_key, db_session) 
                for header_key in header_list
            ]
        )

    return table_dict

def fetch_viewable_value(instance: Base, key: str, db_session: Session) -> str:
    """
    :return: a string representation of the value of the key in the instance.
    """
    property = getattr(instance, key)
    if property is None:
        value = ''
    elif isinstance(property, Enum):
        value = _(property.name, dbman_dict_name_list)
    elif isinstance(property, Base):
        pks = ','.join([str(getattr(property, pk.key)) for pk in property.__mapper__.primary_key])
        url = url_for(
            'base.crud.view_record', 
            table_name=property.__tablename__, # type: ignore
            pks=pks
        )
        value = f'<a href="{url}">{property._name}</a>' # type: ignore
    elif isinstance(property, DataJson):
        value = fetch_json_viewer(property, mode='compact', db_session=db_session)
    else:
        value = str(property)
    return value

def fetch_json_viewer(
        datajson_obj: DataJson, 
        mode:str = 'compact', 
        db_session: Session | None = None
    ) -> str:
    """
    :return: a string representation of the DataJson object.
    """
    if not isinstance(datajson_obj, DataJson):
        raise TypeError(f"Expected DataJson object, got {type(datajson_obj)}")
    rel_info = datajson_obj.rel_info
    entries = []
    for key in datajson_obj.get_keys('data') - datajson_obj.get_keys('hidden'):
        if key in rel_info:
            if db_session is None:
                raise ValueError("db_session is required for relationship resolution")
            pk = getattr(datajson_obj, rel_info[key]['local_col']) # type: ignore
            if pk is None or pk == '':
                continue
            Model = rel_info[key]['ref_table']
            ref_instance = db_session.get(Model, pk) # type: ignore
            if ref_instance is None:
                continue
            ref_url = url_for(
                'base.crud.view_record', 
                table_name=Model.__tablename__, # type: ignore
                pks=str(pk)
            )
            value = f'<a href="{ref_url}">{ref_instance._name}</a>' # type: ignore
        else:
            value = getattr(datajson_obj, key)
            if isinstance(value, Enum):
                value = _(value.name, dbman_dict_name_list)
            elif isinstance(value, (list, set, tuple)):
                value = ', '.join([str(v) for v in value])
            elif isinstance(value, dict):
                value = '{' + ', '.join([f'{k}: {v}' for k, v in value.items()]) + '}'
            elif isinstance(value, DataJson):
                value = '{' + fetch_json_viewer(value, mode='compact', db_session=db_session) + '}'
            elif isinstance(value, str):
                value = f'{value!r}'
            else:
                value = str(value)
        if mode == 'compact':
            entries.append(f'{_(key, dbman_dict_name_list)}: {value}')
    return ', '.join(entries)

def fetch_model_viewer(instance: Base, db_session: Session, header_list: list[str] | None = None):
    if header_list is None:
        header_list = instance.get_headers()
    return {
        _(header, dbman_dict_name_list): fetch_viewable_value(instance, header, db_session) 
        for header in header_list
    }

def fetch_tablename_url_name(instance: Base, table_name: str) -> tuple[str, str, str]:
    """
    :return: an url linking to the instance and string representation of the instance name.
    """
    pks = ','.join([str(i) for i in inspect(instance).identity]) # type: ignore
    name = instance._name # type: ignore
    url = url_for(
        'base.crud.view_record', 
        table_name=table_name,
        pks=pks
    )
    return (_(table_name, dbman_dict_name_list), url, name)

def fetch_related_objects(instance: Base, db_session: Session) -> dict[str, Any]:
    """
    :return: a dict of related objects for the instance.
    """
    related_objects = dict()
    related_objects['single'] = rs = dict()
    related_objects['multiple'] = rm = dict()

    for rel in instance.__class__.__mapper__.relationships:
        if rel.uselist:
            instance_list = getattr(instance, rel.key)
            table_name = instance_list[0].__class__.__tablename__
            rm[_(rel.key, dbman_dict_name_list)] = [
                fetch_tablename_url_name(ref_instance, table_name)
                for ref_instance in instance_list ]
        else:
            rs[_(rel.key, dbman_dict_name_list)] = fetch_tablename_url_name(
                    getattr(instance, rel.key), rel.entity.class_.__tablename__
            )
            
    return related_objects

def fetch_select_list(Model: type[Base], db_session: Session, order_by: Any = None) -> list[tuple[str, str]]:
    """
    :return: a list of tuples containing the primary key and name of the Model.
    """
    stmt = select(*Model.__mapper__.primary_key, Model._name) # type: ignore
    if order_by:
        stmt = stmt.order_by(*order_by) # type: ignore
    result = db_session.execute(stmt)
    pks_name_list = []
    for row in result:
        pks = ','.join([str(pk) for pk in row[:-1]])
        pks_name_list.append((pks, row[-1]))
    return pks_name_list

def fetch_select_options(Model:type[Base] | type[DataJson], db_session:Session) -> dict[str, list[tuple[Any, str]]]:
    """
    :return: a dict of select options for each relationship and enum type column

        - key: local column name 
        - value: [tuple[referenced pk value, referenced column value]]. Values are ordered according to key_info['rel_info'][local_col]['select_order']
    """
    
    select_options = dict()
    if issubclass(Model, Base):
        # Extract foreign key col and referenced pks and name tuple for each relationship
        mapper = Model.__mapper__
        for rel in mapper.relationships:
            pks_name_list = []
            if rel.uselist:
                continue
            ref_Model = rel.entity.class_
            local_col_key = next(iter(rel.local_columns)).key
            select_order = rel.info.get('select_order', None)
            pks_name_list = fetch_select_list(ref_Model, db_session, order_by=select_order) 
            select_options[local_col_key] = pks_name_list
        
        # Extract Enum types and get options from Enum definition
        enum_keys = Model.get_keys('Enum')
        for key in enum_keys:
            attr = getattr(Model, key)
            enum_Model = attr.type.python_type
            if not issubclass(enum_Model, Enum):
                raise AttributeError(f'Invalid enum_Model {enum_Model} for {Model}')
            value_name_list = [(member.value, _(member.name, dbman_dict_name_list)) for member in enum_Model]
            select_options[key] = value_name_list       
    elif issubclass(Model, DataJson):
        for rel_key, rel_info in Model.key_info.get('rel_map', dict()).items(): # type: ignore
            ref_Model = rel_info.get('ref_table')
            local_col_key = rel_info.get('local_col')
            select_order = rel_info.get('select_order', None)
            pks_name_list = fetch_select_list(ref_Model, db_session, order_by=select_order) 
            select_options[local_col_key] = pks_name_list
        # Extract Enum types and get options from Enum definition
        enum_keys = Model.get_keys('Enum')
        for key in enum_keys:
            attr = getattr(Model, key)
            if not isinstance(attr, Enum):
                raise AttributeError(f'Invalid enum_key {key} for {Model}')
            value_name_list = [(member.value, _(member.name, dbman_dict_name_list)) for member in type(attr)]
            select_options[key] = value_name_list
    else:
        raise TypeError(f'Invalid Model type {Model}')
    return select_options

def fetch_datajson_structure(Model: type[DataJson], db_session:Session) -> dict[str, Any]:
    """
    :return: dict of structure of the DataJson class
    - keys: data, required, readonly, date, Enum, foreign_keys, longtext
    - values: list of keys in the class
    """
    struct = dict()
    if Model == DataJson:
        raise AttributeError('Cannot call fetch_structure() on DataJson')
    
    struct['__datajson_id__'] = Model.__datajson_id__
    struct['data'] = [key for key in Model.key_info['data'] if key not in Model.get_keys('single_rel')]
    struct['required'] = Model.get_keys('required')
    struct['readonly'] = Model.get_keys('readonly')
    struct['date'] = Model.get_keys('date')
    struct['longtext'] = Model.get_keys('longtext')
    struct['constraints'] = Model.key_info.get('constraints', dict())
    struct['select_options'] = fetch_select_options(Model, db_session=db_session)
    struct['col_rel_map'] = Model.get_col_rel_map()
    return struct

def fetch_modify_form_viewer(
        instance: Base, 
        db_session: Session, 
    ) -> dict[str, Any]:
    """
    :return: a dict of data for the modify form.

    .. example::
    ```python
        data = fetch_modify_form_viewer(instance, db_session)
        data = {
            'name': ('text', 'Name', 'John Doe', IsRequired:bool),
            'agelevel': ('select', 'Age', 1, False, [(1, '10'), (2, '20')]),
            'address': ('textarea', 'My Address', '123 Main St', False),
            'is_active': ('checkbox', 'If Active', True, False),
            'created_at': ('date', 'Create Date', datetime.now(), False),
            'clause_json': ('DataJson', 'Structured Clause Data', {'key': 'value'}, False)
        }
    ```
    """
    data = dict()
    col_rel_map = instance.get_col_rel_map()
    mod_keys = instance.get_keys('modifiable')
    required_keys = instance.get_keys('required')
    json_keys = instance.get_keys('DataJson')
    longtext_keys = instance.get_keys('longtext')
    select_options = fetch_select_options(instance.__class__, db_session=db_session)

    for key in [key for key in instance.key_info['data'] if key in mod_keys]:
        is_required = key in required_keys
        value = getattr(instance, key) or ''
        if key in col_rel_map:
            name = _(col_rel_map[key], dbman_dict_name_list)
            tag = 'select'
            options = select_options[key]
            data[key] = (tag, name, value, is_required, options)
        else:
            name = _(key, dbman_dict_name_list)
            if isinstance(value, Enum):
                tag = 'select'
                value = value.value
                options = select_options[key]
                data[key] = (tag, name, value, is_required, options)
            else:
                if isinstance(value, date):
                    tag = 'date'
                    value = value.isoformat()
                elif key in longtext_keys:
                    tag = 'textarea'
                elif key in json_keys:
                    tag = 'DataJson'
                    value = value.dumps() if value else ''
                else:
                    tag = 'text'
                data[key] = (tag, name, value, is_required)
    return data