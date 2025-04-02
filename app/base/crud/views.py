# app/base/crud/views.py
# python

from sqlite3 import DatabaseError
from typing import Any
# flask
from flask import render_template, request, jsonify, abort, url_for
# sqlalchemy

# app
from config import Config
from app import _
from app.utils.templates import PageNavigation
from app.extensions import db_session, Base


navigation = PageNavigation ({
    '_homepage': '/',
    '_crud': '/crud'
})

def index() -> Any:
    table_names = Base.model_map.keys()
    return render_template(
        'crud/index.jinja',  
        table_names=table_names, 
        navigation=navigation.index
    )

def view_table(table_name: str) -> Any:
    if table_name not in Base.model_map:
        abort(404)
    Model = Base.model_map[table_name]
    with db_session() as db_sess:
        Base.db_session = db_sess
        data_dict = Model.fetch_datatable_dict()

    return render_template(
        'crud/view_table.jinja',
        navigation = navigation.get_nav({'View table': '#'}), 
        table_names=Base.model_map.keys(), 
        table_name=table_name,
        data=data_dict,
        dbman_dict_name_list=Config.DATABASE_NAMES.split(',') if Config.DATABASE_NAMES else None
    )

def modify_record(table_name: str, pks: str) -> Any:
    with db_session() as db_sess:
        Base.db_session = db_sess
        model = fetch_model(table_name, pks)
        if request.method == 'GET': 
            select_options = model.fetch_select_options()
            datajson_ref_map = model.fetch_datajson_ref_map()
        elif request.method == 'POST':
            try:
                model.replace_data(request.form.to_dict())
                if pks == '_new':
                    db_sess.add(model)
                db_sess.commit()
                return jsonify(success=True), 200
            except Exception as e:
                db_sess.rollback()
                return jsonify(success=False, error=str(e)), 500
        else:
            abort(404)

    # runs to this line only if request.method == 'GET'
    if pks == '_new':
        data = dict()
    else:
        data = model.data_dict(serializeable=True)
    headers = model.get_headers()

    return render_template(
        'crud/modify_record.jinja',
        navigation=navigation.get_nav({'Modify record': '#'}), 
        table_name=table_name, 
        pks=pks,
        select_options=select_options, # type: ignore
        date_keys=model.get_col_keys('date'),
        datajson_ref_map=datajson_ref_map, # type: ignore
        required_keys=model.get_col_keys('required'),
        readonly_keys=model.get_col_keys('readonly'),
        longtext_keys=model.get_col_keys('longtext'),
        headers=headers,
        data=data
    )

def delete_record(table_name: str, pks: str) -> Any:
    if request.method != 'DELETE':
        abort(404)
    if table_name not in Base.model_map:
        abort(404)
    Model = Base.model_map[table_name]
    pks_tuple = tuple(pks.split(','))

    with db_session() as sess:
        model = sess.get(Model, pks_tuple)
        if model:
            sess.delete(model)
        try:
            sess.commit()
            return jsonify(success=True), 200 
        except Exception as e:  
            sess.rollback()
            return jsonify(success=False, error=str(e)), 500
        
def view_record(table_name: str, pks: str) -> str:
    with db_session() as db_sess:
        Base.db_session = db_sess
        model = fetch_model(table_name, pks)
        rel_data = model.fetch_rel_data(with_lists=True, with_data=True)

    headers = model.get_headers()
    basic_info = model.data_dict(serializeable=True)
    return render_template(
        'crud/view_record.jinja', 
        table_name=table_name,
        pks=pks,
        basic_info=basic_info,
        headers=headers,
        rel_data=rel_data,
        dbman_dict_name_list=Config.DATABASE_NAMES.split(',') if Config.DATABASE_NAMES else None,
        navigation=navigation.get_nav({
            'View table': url_for('base.crud.view_table', table_name=table_name),
            'View record': '#'
        })
    )

def fetch_model(table_name: str, pks: str) -> Base:
    """
    Fetch a model instance from the database based on the table name and pks (primary keys).
    If pks is '_new', a new instance of the model is created.
    .. attention:: Base.db_session must be initialized before calling this function.

    :returns: A Base model derived from DeclarativeBase.
    :param table_name: The name of the table to fetch the model from.
    :param pks: The primary keys joined by comma. If pks is '_new', a new instance is created.
    :raises: 404 if the table name is not found or the model instance is not found.
    
    *example*:
    ```python
    model = fetch_model('user', '1,2')
    model = fetch_model('user', '_new')
    ```
    """
    if table_name not in Base.model_map or pks is None:
        abort(404)
    Model = Base.model_map[table_name]
    if pks == '_new':
        model = Model()
    else:
        pk_value_tuple = tuple(pks.split(','))
        if not Base.db_session:
            raise DatabaseError(f'Base.db_session not initialized {Base.db_session}')
        model = Base.db_session.get(Model, pk_value_tuple)
    if model is None:
        abort(404)
    return model
