# app/base/admin/views.py
from datetime import datetime
import json
from app import _
from flask import render_template, request, jsonify
from sqlalchemy import select
from app.extensions import db_session, DBModel, ForeignKeyMixin, EXTModel

navigation = {'_homepage':'/', '_admin': '/admin'}

def admin_index():
    table_names = DBModel.keys()
    return render_template(
        'admin/index.html',  
        table_names=table_names, 
        navigation=navigation)

def view_table(table_name):
    """查看表数据"""
    if table_name not in DBModel:
        return _('_table_not_found'), 404
    Model = DBModel[table_name]
    with db_session() as sess:
        models = sess.scalars(select(Model)).all()
    prop_info = Model.get_prop_info(data_style='rel_name', exclude_info={'hidden'})
    theads = [pi['key'] for pi in prop_info]
    nav = navigation.copy()
    nav['View Table'] = '#'
    return render_template(
        'admin/view_table.html',
        navigation = nav, 
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
