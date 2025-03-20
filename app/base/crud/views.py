# app/base/crud/views.py
# python
from typing import Any
# flask
from flask import render_template, request, jsonify, abort
# app
from app import _
from app.utils.templates import PageNavigation
from app.extensions import db_session, Base

# 本蓝图的基础导航
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

def modify_record(table_name, pks):
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
        if request.method == 'POST':
            try:
                model.replace_data(request.form.to_dict())
                if pks == '_new':
                    db_sess.add(model)
                db_sess.commit()
                return jsonify(success=True), 200
            except Exception as e:
                db_sess.rollback()
                return jsonify(success=False, error=str(e)), 500
        
        # method == GET
        ref_names = Model.fetch_ref_names()
        date_keys = Model.get_col_keys('date')
        json_keys = Model.get_col_keys('json')
        required_keys = Model.get_col_keys('required')
        readonly_keys = Model.get_col_keys('readonly')
        if pks == '_new':
            data = dict()
        else:
            data = model.data_dict(serializeable=True)
    
    return render_template(
        'crud/modify_record.jinja',
        navigation=navigation.get_nav({'Modify record': '#'}), 
        table_name=table_name, 
        model=model,
        pks=pks,
        ref_names=ref_names,
        date_keys=date_keys,
        json_keys=json_keys,
        required_keys=required_keys,
        readonly_keys=readonly_keys,
        data=data
    )

def delete_record(table_name, record_id):
    if request.method != 'DELETE':
        abort(404)
    if table_name not in Base.model_map:
        abort(404)
    Model = Base.model_map[table_name]
    pks = tuple(record_id.split(','))

    with db_session() as sess:
        model = sess.get(Model, pks)
        if model:
            sess.delete(model)
        try:
            sess.commit()
            return jsonify(success=True), 200 
        except Exception as e:  
            sess.rollback()
            return jsonify(success=False, error=str(e)), 500
        
def view_record(table_name: str, record_id: str) -> Any:
    pass
