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
    hidden_attrs = Model.attr_info.get('hidden', [])
    if not pk_attrs:
        abort(404)
    with db_session() as sess:
        # 查询表的所有记录，默认把有ref_name的列替换为引用表对应的ref_name列
        result = sess.execute(data_query)
    pks = []
    pks, data = Model.split_result(result)
    results_keys = result.keys()
    theads = [key for key in results_keys if key not in hidden_attrs]
    for key in results.keys():
        col_info = col_infos.get(key)
        # (not col_info)表示该列为其他表的关联列，
        # (not col_info.get('hidden')表示要排除hidden属性的列
        if not col_info or not col_info.get('hidden'):
            theads.append(key)
        if col_info and col_info.get('PK'):
            pk_col_keys.append(key)
    data = []
    pk_data = []
    for row in results:
        pk_row = []
        data_row = []
        col_num = 0
        for key in results.keys():
            value = row[col_num]
            if key in pk_col_keys:
                pk_row.append(value)
            if key in theads:
                data_row.append(value)
            col_num += 1
        pk_row_concat = ','.join(map(str, pk_row))
        pk_data.append(pk_row_concat)
        data.append(data_row)
    return render_template(
        'crud/view_table.jinja',
        navigation = navigation.get_nav({'View table': '#'}), 
        table_names=DBModel.keys(), 
        table_name=table_name,
        pk_data=pk_data,
        theads=theads, 
        data=data, 
        col_infos=col_infos
    )

def modify_record(table_name, pks):
    if table_name not in DBModel:
        abort(404)
    Model = DBModel[table_name]
    col_infos = Model.get_col_infos()
    if request.method == 'POST':
        form_data = request.form.to_dict()
        pks = request.form.get('_pks')
        form_data.pop('_pks', None)
        for key, value in form_data.items():
            col_info = col_infos.get(key)
            if value == '':
                form_data.pop(key, None)
            elif col_info.get('Date'):
                form_data[key] = datetime.strptime(value, '%Y-%m-%d').date()
        with db_session() as sess:
            if pks != '_new':
                model = sess.get(Model, pks)
                
            else:
                model = Model(**form_data)
                sess.add(model)
            try:
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
    pks = record_id.split(',')
    with db_session() as sess:
        model = sess.get(Model,*pks)
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
