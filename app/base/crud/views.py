# app/base/crud/views.py
# python
from typing import Any
from webbrowser import get
# flask
from flask import render_template, request, jsonify, abort, url_for
# app
from app import _
from app.utils.templates import PageNavigation
from app.extensions import db_session, Base, DataJson


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
    """查看表数据"""
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
        data=data_dict
    )

def modify_record(table_name: str, pks: str) -> Any:
    model = get_model(table_name, pks)
    if request.method == 'POST':
        with db_session() as db_sess:
            try:
                Base.db_session = db_sess
                model.replace_data(request.form.to_dict())
                if pks == '_new':
                    db_sess.add(model)
                db_sess.commit()
                return jsonify(success=True), 200
            except Exception as e:
                db_sess.rollback()
                return jsonify(success=False, error=str(e)), 500
        
    # request.method == GET
    pk_keys = model.get_col_keys('pk')
    
    data = model.data_dict(serializeable=True)
    headers = model.get_headers()
    
    return render_template(
        'crud/modify_record.jinja',
        navigation=navigation.get_nav({'Modify record': '#'}), 
        table_name=table_name, 
        pks=pks,
        select_options=model.fetch_col_select_options(),
        date_keys=model.get_col_keys('date'),
        datajson_ref_map=model.fetch_datajson_ref_map(),
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
        
def view_record(table_name: str, pks: str) -> Any:
    model = get_model(table_name, pks)
    basic_info = model.data_dict(serializeable=True)


    return render_template(
        'crud/view_record.jinja', 
        table_name=table_name, 
        pks=pks,
        basic_info=basic_info,
        headers=model.get_headers(),
        navigation=navigation.get_nav({
            'View table': url_for('base.crud.view_table', table_name=table_name),
            'View record': '#'
        })
    )

def get_model(table_name: str, pks: str) -> Any:
    if table_name not in Base.model_map or pks is None:
        abort(404)
    Model = Base.model_map[table_name]
    with db_session() as db_sess:
        Base.db_session = db_sess
        if pks == '_new':
            model = Model()
        else:
            pk_value_tuple = tuple(pks.split(','))
            model = db_sess.get(Model, pk_value_tuple)
        if model is None:
            abort(404)
    return model