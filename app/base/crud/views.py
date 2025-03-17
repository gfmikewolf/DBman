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
    if table_name not in Base.model_map:
        abort(404)
    Model = Base.model_map[table_name]
    if request.method == 'POST':
        form_data = request.get_json(silent=True)
        if form_data is None:
            abort(404)
        _pks = form_data.get('_pks', None)
        if pks is None:
            abort(404)
        form_data.pop('_pks', None)
        pks = Model.retrieve_tuple_pks(_pks)
        
        with db_session() as sess:
            try:
                if _pks == '_new':
                    model = Model(form_data)
                    sess.add(model)
                else:
                    model = sess.get(Model, pks)
                    if model is None:
                        return jsonify({
                            'status': 'error', 
                            'message': _('Missing record')
                        }), 404
                    model.update_from_form(form_data)
                sess.commit()
                return jsonify({
                    'status': 'success', 
                    'message': _('Successfully saved changes')
                })
            except Exception as e:
                sess.rollback()
                msg = _('_failedto save changes')
                err = _('Error')
                return jsonify({
                    'status': 'error', 
                    'message': f'{msg}: {err} {str(e)}'
                }), 500

    
    prop_info = Model.get_prop_info(exclude_info={'readonly'})
    
    with db_session() as sess:
        options_fk = {}
        if issubclass(Model, ForeignKeyMixin):
            options_fk = Model.get_options_fk(sess)
        if record_id != '_new':
            model = sess.get(Model, record_id)
        else:
            model = None
    return render_template(
        'crud/modify_record.html', 
        table_name=table_name, 
        model=model,
        record_id=record_id,
        options_fk=options_fk, 
        prop_info=prop_info
    )

def delete_record(table_name, record_id):
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
            return jsonify({
                'status': 'success', 
                'message': _('Successfully deleted the record')
            })
        except Exception as e:  
            sess.rollback()
            return jsonify({
                'status': "error",
                "message": _('_failedto delete the record')
            }), 500
