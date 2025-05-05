# app/base/crud/utils.py

__all__ = [
    'fetch_instance',
    'fetch_tabledata',
    'fetch_viewable_value',
    'fetch_json_viewer',
    'fetch_model_viewer',
    'fetch_tablename_url_name',
    'fetch_related_objects',
    'fetch_select_list',
    'fetch_select_options',
    'fetch_datajson_structure',
    'fetch_modify_form_viewer',
    'fetch_related_funcs'
]

from inspect import signature
from math import e
from operator import call
from shlex import join
from typing import Any, Iterable
from enum import Enum
from flask import abort, url_for, session as app_session
from numpy import isin
from requests import get
from sqlalchemy import select, inspect
from sqlalchemy.orm import Session
from app.base.auth.privilege import Privilege
from app.utils import _
from app.extensions import Base
from app.database.base import DataJson

_default_viewer = 'base.crud.view_record'
_default_link_target = None

def get_rel_select_tuple(func: Any, instance: Base | None = None) -> Any:
    """
    Call a function with the given arguments and keyword arguments.
    If the function raises an exception, return None.
    """
    obj = None
    if callable(func):
        sig = signature(func)
        if len(sig.parameters) == 1:
            if instance is None:
                raise TypeError(f"Function {func} requires an instance as an argument")
            obj = func(instance)
        else:
            obj = func()
        if not isinstance(obj, tuple):
            obj = (obj, )
    else:        
        obj = func if isinstance(func, tuple) else (func, )
    return obj

def fetch_instance(table_name: str, pks: str, db_session: Session) -> Base:
    """
    Fetch a model instance from the database based on the table name and pks (primary keys).

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
        return Model()
    pk_value_tuple = tuple(pks.split(','))
    instance = db_session.get(Model, pk_value_tuple)
    if instance is None:
        abort(404)
    return instance
def fetch_tabledata(Model: type[Base], db_session: Session) -> dict[str, Any]:
    """
    :return: a select statement for all rows in the table.

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
        _(header_key, True)
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
def get_viewable_instance_name(instance: Base) -> str:
    if '_self' in instance.get_keys('translate'):
        return _(str(instance), True)
    else:
        return str(instance)
def get_viewable_instance(instance: Base, viewer: str = _default_viewer, target: str | None = _default_link_target) -> str:
    pks = ','.join([str(getattr(instance, pk.key)) for pk in instance.__mapper__.primary_key])
    url = url_for(
        viewer, 
        table_name=instance.__tablename__, # type: ignore
        pks=pks
    )
    return f'<a href="{url}" class="dbman-link"{f' target="{target}"' if target else '' }>{get_viewable_instance_name(instance)}</a>' # type: ignore
def fetch_viewable_value(instance: Base, key: str, db_session: Session, viewer: str = _default_viewer, target: str | None = _default_link_target) -> str:
    """
    :return: a string representation of the value of the key in the instance.
    """
    property = getattr(instance, key, None)
    if property is None or property == '':
        return ''
    translate_keys = instance.get_keys('translate')
    if isinstance(property, (list, set, tuple)):
        if len(property) == 0:
            return ''
        sample = next(iter(property))
        if isinstance(sample, Base):
            value = ', '.join([
                get_viewable_instance(prop, viewer, target)
                for prop in property               
            ])
        else:
            value = ', '.join(map(str, property))
            if key in translate_keys:
                value = _(value, True) 
    elif isinstance(property, Enum):
        value = _(property.value, True)
    elif isinstance(property, Base):
        value = get_viewable_instance(property, viewer, target)
    elif isinstance(property, DataJson):
        value = fetch_json_viewer(property, mode='compact', db_session=db_session)
    elif isinstance(property, float):
        value = f'{property:,.2f}'
    else:
        value = str(property)
        if key in translate_keys:
            value = _(value, True)
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
    entries = []
    rel_info = datajson_obj.rel_info
    for key in datajson_obj.get_keys('data') - datajson_obj.get_keys('hidden'):
        if key in rel_info:
            value = getattr(datajson_obj, rel_info[key]['local_col'], None) # type: ignore
            if value is None or value == '':
                continue
            if db_session is None:
                raise ValueError("db_session is required for relationship resolution")    
            Model = datajson_obj.rel_info[key]['ref_table']
            ref_instance = db_session.get(Model, value) # type: ignore
            if ref_instance is None:
                continue
            ref_url = url_for(
                'base.crud.view_record', 
                table_name=Model.__tablename__, # type: ignore
                pks=str(value)
            )
            value = f'<a href="{ref_url}" class="link-offset-3">{get_viewable_instance_name(ref_instance)}</a>' # type: ignore
        else:
            value = getattr(datajson_obj, key, None)
            if value is None or value == '':
                continue
            if isinstance(value, Enum):
                value = _(value.name, True)
            elif isinstance(value, (list, set, tuple)):
                value = ', '.join([str(v) for v in value])
            elif isinstance(value, dict):
                value = '{' + ', '.join([f'{k}: {v}' for k, v in value.items()]) + '}'
            elif isinstance(value, DataJson):
                value = '{' + fetch_json_viewer(value, mode='compact', db_session=db_session) + '}'
            elif isinstance(value, str):
                value = f'{value}'
            else:
                value = str(value)
        if mode == 'compact':
            entries.append(f'{_(key, True)}: {value}')
    return ', '.join(entries)
def fetch_model_viewer(instance: Base, db_session: Session, header_list: list[str] | None = None, viewer: str = _default_viewer, target: str | None = _default_link_target) -> dict[str,Any]:
    if header_list is None:
        header_list = instance.get_headers()
    return {
        _(header, True): fetch_viewable_value(instance, header, db_session, viewer, target) 
        for header in header_list
    }
def fetch_tablename_url_name(instance: Base, table_name: str, viewer:str = _default_viewer) -> tuple[str, str, str]:
    """
    :return: an url linking to the instance and string representation of the instance name.
    """
    if instance is None:
        return('', '#', '')
    pks = ','.join([str(i) for i in inspect(instance).identity]) # type: ignore
    name = get_viewable_instance_name(instance)
    url = url_for(
        viewer, 
        table_name=table_name,
        pks=pks
    )
    return (_(table_name, True), url, name)
def get_poly_index_map(instance_list: Iterable[Base]) -> dict[str, int]:
    """
    :return: a dict of index for polymorphic instances.
    { 'tablename': [1, 2, 3...], ... }
    """
    polyid_ids_map = dict()
    for i, instance in enumerate(instance_list):
        tn = instance.__tablename__
        if tn in polyid_ids_map:
            polyid_ids_map[tn].append(i)
        else:
            polyid_ids_map[tn] = [i]
    return polyid_ids_map
def fetch_related_objects(instance: Base, db_session: Session, viewer: str = _default_viewer) -> dict[str, Any]:
    """
    :return: a dict of related objects for the instance.

    .. attention:: 
    Active session is required to access list relationships

    """
    related_objects = dict()
    related_objects['single'] = rs = dict()
    related_objects['multiple'] = rm = dict()

    roles = {k.split('_')[-1] for k in instance.key_info if k.startswith('_rv_')}
    role_keys = set()
    for role in roles:
        if Privilege.session_match(role):
            role_keys.update(instance.key_info.get(f'_rv_{role}', set()))
    mkeys = instance.get_keys('viewable_list') | role_keys
    shown = set()
    for rel in instance.__class__.__mapper__.relationships:
        if rel.uselist:
            if rel.key not in mkeys:
                continue
            instance_list = getattr(instance, rel.key)
            if len(instance_list) == 0:
                db_session.refresh(instance, attribute_names=[rel.key])
                if len(instance_list) == 0:
                    continue
            sample_cls = instance_list[0].__class__
            sample_cls = sample_cls.get_polymorphic_base() or sample_cls
            table_name = sample_cls.__tablename__
            kwgs = {}
            if rel.secondary is None:
                for local_col, remote_col in zip(rel.local_columns, rel.remote_side):
                    local_val = getattr(instance, local_col.name, None)
                    if local_val is not None:
                        kwgs[remote_col.name] = local_val
            url_add = url_for('base.crud.modify_record', table_name=table_name, pks='_new', **kwgs)
            poly_index_map = get_poly_index_map(instance_list)
            tun = [
                fetch_tablename_url_name(ref_instance, table_name, viewer)
                for ref_instance in instance_list
            ]
            rm[_(rel.key, True)] = (poly_index_map, tun, url_add)
            shown.add(rel.key)
        #else:
        #    rel_prop = getattr(instance, rel.key)
        #    if rel_prop is None:
        #        continue
        #    rs[_(rel.key, True)] = fetch_tablename_url_name(
        #        rel_prop, rel.entity.class_.__tablename__, viewer
        #    )
    
    for key in instance.get_keys('viewable_list') - shown:
        attrs = getattr(instance, key, None)
        if attrs and isinstance(attrs, (list, set, tuple)):
            sample = next(iter(attrs))
            if isinstance(sample, Base):
                poly_index_map = get_poly_index_map(attrs)
                table_name = sample.__class__.__tablename__
                url_add = url_for('base.crud.modify_record', table_name=table_name, pks='_new')
                tun = [
                    fetch_tablename_url_name(attr, table_name, viewer)
                    for attr in attrs
                ]
                rm[_(key, True)] = (
                    poly_index_map, 
                    [
                        fetch_tablename_url_name(attr_instance, table_name, viewer)
                        for attr_instance in attrs
                    ],
                    url_add
                )
            else:
                rm[_(key, True)] = (
                    {},
                    list(attrs),
                    None
                )
    return related_objects
def fetch_select_list(Model: type[Base], db_session: Session, instance: Base | None = None, info: dict[str, Any] = {}) -> list[tuple[str, str]]:
    """
    :return: a list of tuples containing the primary key and name of the Model.
    """
    stmt = select(Model)
    join_clause = info.get('join', None)
    order_by = info.get('order_by', None)
    where_clause = info.get('where', None)
    if join_clause:
        for jc in get_rel_select_tuple(join_clause, instance):
            stmt = stmt.join(*jc)
    if order_by:
        stmt = stmt.order_by(*get_rel_select_tuple(order_by, instance))
    if where_clause:
        stmt = stmt.where(*get_rel_select_tuple(where_clause, instance))
    if info.get('distinct', False):
        stmt = stmt.distinct()
    if info.get('limit', False):
        stmt = stmt.limit(info['limit'])
    if info.get('offset', False):
        stmt = stmt.offset(info['offset'])
    models = db_session.scalars(stmt).all()
    pks_name_list = []
    for model in models:
        pks = ','.join([str(pk) for pk in inspect(model).identity]) # type: ignore
        name = _(str(model), True) if '_self' in Model.get_keys('translate') else str(model)
        pks_name_list.append((pks, name))
    return pks_name_list
def fetch_select_options(Model:type[Base] | type[DataJson], db_session: Session, polymorphic_spec_only: bool = False, instance: Base | None = None) -> dict[str, list[tuple[Any, str]]]:
    """
    :return: a dict of select options for each relationship and enum type column

        - key: local column name 
        - value: [tuple[referenced pk value, referenced column value]]. Values are ordered according to key_info['rel_info'][local_col]['select_order']
    """
    
    select_options = dict()
    base_data_keys = set()
    if polymorphic_spec_only:
        base_data_keys = Model.get_keys('polybase_data')
    polymorphic_spec_only = polymorphic_spec_only and bool(base_data_keys)
    if issubclass(Model, Base):
        # Extract foreign key col and referenced pks and name tuple for each relationship
        mapper = Model.__mapper__
        for rel in mapper.relationships:
            pks_name_list = []
            if rel.uselist or rel.secondary is not None:
                continue
            ref_Model = rel.entity.class_
            local_col_key = next(iter(rel.local_columns)).key
            if local_col_key in base_data_keys:
                continue
            pks_name_list = fetch_select_list(
                ref_Model, 
                db_session,
                instance=instance,
                info=rel.info
            ) 
            select_options[local_col_key] = pks_name_list
        
        # Extract Enum types and get options from Enum definition
        enum_keys = Model.get_keys('Enum') - base_data_keys
        for key in enum_keys:
            attr = getattr(Model, key)
            enum_Model = attr.type.python_type
            if not issubclass(enum_Model, Enum):
                raise AttributeError(f'Invalid enum_Model {enum_Model} for {Model}')
            value_name_list = [(member.name, _(member.value, True)) for member in enum_Model]
            select_options[key] = value_name_list       
    elif issubclass(Model, DataJson):
        for rel_key, rel_info in Model.rel_info.items(): # type: ignore
            ref_Model = rel_info.get('ref_table')
            local_col_key = rel_info.get('local_col')
            s_join = rel_info.get('join', None)
            s_order_by = rel_info.get('order_by', None)
            s_where = rel_info.get('where', None)
            pks_name_list = fetch_select_list(
                ref_Model, # type: ignore
                db_session,
                info=rel_info
            )
            select_options[local_col_key] = pks_name_list
        # Extract Enum types and get options from Enum definition
        enum_keys = Model.get_keys('Enum')
        for key in enum_keys:
            attr = getattr(Model, key)
            if not isinstance(attr, Enum):
                raise AttributeError(f'Invalid enum_key {key} for {Model}')
            value_name_list = [(member.name, _(member.value, True)) for member in type(attr)]
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
    struct['data'] = [key for key in Model.data_list if key not in Model.get_keys('single_rel')]
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
        initial_data: dict = dict()
    ) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    :return: a dict of data for the modify form.

    .. example::
    ```python
        base_data, spec_data = fetch_modify_form_viewer(instance, db_session)
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
    spec_data = dict()
    base_data_keys = instance.get_keys('polybase_data')
    col_rel_map = instance.get_col_rel_map()
    select_options = fetch_select_options(instance.__class__, db_session, instance=instance)
    required_keys = instance.get_keys('required')
    enum_keys = instance.get_keys('Enum')
    date_keys = instance.get_keys('date')
    longtext_keys = instance.get_keys('longtext')
    datajson_keys = instance.get_keys('DataJson')
    password_keys = instance.get_keys('password')
    
    for key in [
        key for key in instance.data_list 
        if key in instance.get_keys('modifiable')
    ]:
        if key in initial_data:
            value = initial_data[key]
        else: 
            value = getattr(instance, key, None)
            if value is None:
                value = ''
        is_required = key in required_keys
        if key in col_rel_map:
            name = _(col_rel_map[key], True)
            tag = 'select'
            options = select_options[key]
            r = (tag, name, str(value), is_required, options)
        else:
            name = _(key, True)
            if key in enum_keys:
                tag = 'select'
                if value:
                    value = value.name # type: ignore
                options = select_options[key]
                r = (tag, name, value, is_required, options)
            else:
                if key in date_keys:
                    tag = 'date'
                    try:
                        value = value.isoformat() # type: ignore
                    except:
                        value = ''
                elif key in longtext_keys:
                    tag = 'textarea'
                elif key in datajson_keys:
                    tag = 'DataJson'
                    value = value.dumps() if value else ''
                elif key in password_keys:
                    tag = 'password'
                    value = ''
                else:
                    tag = 'text'
                r = (tag, name, value, is_required)
        if key in base_data_keys:
            data[key] = r
        else:
            spec_data[key] = r
    return data, spec_data
def fetch_related_funcs(table_name: str, db_session: Session, func_type: str = 'class') -> dict[str, Any]:
    """
    :return: a dict of related functions for the table.
    """
    if table_name not in Base.func_map:
        return dict()
    func_inputs = dict()
    for func_name, func_info in Base.func_map[table_name].items():
        if func_info['func_type'] != func_type:
            continue
        func_input = dict()
        if func_info['func_type'] == 'instance':
            func_input['_pks'] = (
                'select', # tag
                _(table_name, True), # name
                '', # value
                True, # is_required
                fetch_select_list(Base.model_map[table_name], db_session) # select_list
            )
        for param_name, param_info in func_info['input_types'].items():       
            param_type_info = param_info[0].split('.')
            param_type = param_type_info[0]
            if param_type == '_id':
                select_table = param_type_info[1]
                select_list = fetch_select_list(Base.model_map[select_table], db_session)
                func_input[param_name] = (
                    'select', # tag
                    _(param_name, True), # name
                    '', # value
                    param_info[1], # is_required
                    select_list # select_list
                )
            else: 
                func_input[param_name] = (
                    param_type, # tag
                    _(param_name, True), # name
                    '', # value
                    param_info[1], # is_required
                )
        func_inputs[func_name] = func_input
    return func_inputs
