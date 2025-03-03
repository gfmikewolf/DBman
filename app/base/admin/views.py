# app/base/admin/views.py
from datetime import datetime
import json
from app import _
from flask import render_template, request, jsonify, abort, url_for
from sqlalchemy import select
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty, SynonymProperty
from app.extensions import db_session, DBModel, ForeignKeyMixin, EXTModel

def get_nav(nav_level=None, nav_url=None) -> dict:
    navigation = {
        '_homepage': url_for('base.index'),
        '_admin': url_for('base.admin.admin_index')
    }
    if nav_level and nav_url:
        navigation[nav_level] = nav_url
    return navigation

def admin_index():
    table_names = DBModel.keys()
    return render_template(
        'admin/index.jinja',  
        table_names=table_names, 
        navigation=get_nav())

def view_table(table_name):
    """查看表数据"""
    if table_name not in DBModel:
        abort(404)
    Model = DBModel[table_name]
    with db_session() as sess:
        # 构建一个查询，返回模型的列属性，存在synonym时，只返回synonym而不是真实列名，存在外键对应的关系时，查询关系的.name属性，比如关系是rel，则返回select(..., rel.name)
        query_columns = []
        replaced_columns = []
        mapper = Model.__mapper__
        for col in mapper.columns:
            if col in mapper.primary_key:
                query_columns.append(getattr(Model, col.key, None))
            elif col.foreign_keys:
                ref_name = col.info.get('ref_name')
                if ref_name:
                    
                continue
            if col.foreign_keys:
                ref_name = col.info.get('ref_name')
                if ref_name:
                    query_columns.append(getattr(Model, ref_name, None))
                continue
            elif col.foreign_keys:
                ref_name = prop.info.get('ref_name')
                if ref_name:
                    rel_name = getattr(prop, 'name', None)
                    print(f'\n prop: {prop.key}, \n rel_name: {rel_name}')
                    if rel_name:
                        query_columns.append(rel_name)
                        replaced_columns.append(getattr(Model, int_fk_attr_name, None))
            elif isinstance(prop, ColumnProperty):
                query_columns.append(getattr(Model, prop.key, None))
        # 从query_columns中剔除replaced_columns中的列
        query_columns = [col for col in query_columns if col.key not in replaced_columns]
        print([col.key for col in query_columns])
        print(replaced_columns)
        query = select(*query_columns)
        result = sess.execute(query).all()
        print(result)
        models = sess.scalars(select(Model)).all()
        
    prop_info = Model.get_prop_info(data_style='rel_name', exclude_info={'hidden'})
    theads = [pi['key'] for pi in prop_info]
    return render_template(
        'admin/view_table.jinja',
        navigation = get_nav('View table','#'), 
        table_names=DBModel.keys(), 
        table_name=table_name, 
        theads=theads, 
        models=models, 
        prop_info=prop_info
    )

def modify_record(table_name, record_id):
    if table_name not in DBModel:
        return jsonify({'status': 'error', 'message': 'Table not found'})
    Model = DBModel[table_name]

    if request.method == 'POST':
        form_data = request.form.to_dict()
        record_id = request.form.get('id')
        form_data.pop('id', None)
        form_data_original = form_data.copy()
        for key in form_data_original:
            if form_data_original[key] == '':
                form_data.pop(key, None)
            elif key.endswith('date'):
                form_data[key] = datetime.strptime(form_data[key], '%Y-%m-%d').date()
        with db_session() as sess:
            if record_id != '__new__':
                model = sess.get(Model, record_id)
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
        if record_id != '__new__':
            model = sess.get(Model, record_id)
        else:
            model = None

    return render_template(
        'admin/modify_record.html', 
        table_name=table_name, 
        model=model,
        record_id=record_id,
        options_fk=options_fk, 
        prop_info=prop_info
    )

def delete_record(table_name, record_id):
    if table_name not in DBModel:
        return jsonify({'status': 'error', 'message': _('_table_not_found')})
 
    Model = DBModel[table_name]

    with db_session() as sess:
        model = sess.get(Model, record_id)
        if model:
            sess.delete(model)
            dd = model.data_dict(data_style='rel_name')
            for key in dd:
                value = dd[key]
                if key.endswith('date'):
                    dd[key] = value.strftime('%Y-%m-%d') if value else ''
            msg = json.dumps(dd)
        try:
            sess.commit()
            return jsonify({
                'status': 'success', 
                'message': msg
            })
        except Exception as e:  
            sess.rollback()
            return jsonify({
                'status': "error",
                "message": msg
            }), 500
