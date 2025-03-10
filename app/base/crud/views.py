# app/base/crud/views.py
from datetime import datetime
import json
import logging
from flask import render_template, request, jsonify, abort, url_for
from sqlalchemy import select
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty, SynonymProperty
from app.extensions import db_session, DBModel, Base
from app import _
from app.utils import PageNavigation

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 本蓝图的基础导航
navigation = PageNavigation ({
    '_homepage': '/',
    '_crud': '/crud'
})

Base.models_map = DBModel

def index():
    table_names = DBModel.keys()
    return render_template(
        'crud/index.jinja',  
        table_names=table_names, 
        navigation=navigation.index
    )

def view_table(table_name):
    """查看表数据"""
    if table_name not in DBModel:
        abort(404)
    Model = DBModel[table_name]
    data_query = Model.query_all()
    pk_attrs = Model.attr_info.get('pk', [])

    if not pk_attrs:
        abort(404)
    with db_session() as sess:
        # 查询表的所有记录，默认把有ref_name的列替换为引用表对应的ref_name列
        result = sess.execute(data_query)
    pk_data, theads, json_cols, data = Model.split_result(result)

    return render_template(
        'crud/view_table.jinja',
        navigation = navigation.get_nav({'View table': '#'}), 
        table_names=DBModel.keys(), 
        table_name=table_name,
        pk_data=pk_data,
        theads=theads, 
        data=data, 
        json_cols=json_cols
    )

def modify_record(table_name, pks):
    if table_name not in DBModel:
        abort(404)
    Model = DBModel[table_name]
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
    if table_name not in DBModel:
        abort(404)
    Model = DBModel[table_name]
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
