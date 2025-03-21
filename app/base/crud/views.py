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

def modify_record(table_name: str, pks: str) -> Any:
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
                print(request.form.to_dict())
                model.replace_data(request.form.to_dict())
                print(model.data_dict())
                if pks == '_new':
                    db_sess.add(model)
                db_sess.commit()
                return jsonify(success=True), 200
            except Exception as e:
                db_sess.rollback()
                return jsonify(success=False, error=str(e)), 500
        
        # method == GET
        ref_pks_name = Model.fetch_ref_pks_name()
        date_keys = Model.get_col_keys('date')
        pk_keys = Model.get_col_keys('pk')
        datajson_keys = Model.get_col_keys('DataJson')
        required_keys = Model.get_col_keys('required')
        readonly_keys = Model.get_col_keys('readonly')
        longtext_keys = Model.get_col_keys('longtext')
        
        data = model.data_dict(serializeable=True)
        headers = [
            col.name 
            for col in model.__mapper__.columns 
            if col.name in data.keys() and col.name not in pk_keys
        ]
    
    return render_template(
        'crud/modify_record.jinja',
        navigation=navigation.get_nav({'Modify record': '#'}), 
        table_name=table_name, 
        pks=pks,
        ref_pks_name=ref_pks_name,
        date_keys=date_keys,
        datajson_keys=datajson_keys,
        required_keys=required_keys,
        readonly_keys=readonly_keys,
        longtext_keys=longtext_keys,
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
        
def view_record(table_name: str, record_id: str) -> Any:
    pass
