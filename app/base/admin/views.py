# app/base/admin/views.py
import io
import csv
import json
from flask import g, render_template, request, make_response, jsonify
from sqlalchemy import select
from app.extensions import db_session, DBModel, ForeignKeyMixin

def admin_index():
    table_names = DBModel.keys()
    return render_template('admin/index.html', PageText=g.PageText, table_names=table_names)

def view_table(table_name):
    """查看表数据"""
    if table_name not in DBModel:
        return g.PageText['TableNotFound'], 404
    Model = DBModel[table_name]
    with db_session() as sess:
        models = sess.scalars(select(Model)).all()
    prop_info = Model.get_prop_info(data_style='rel_name', exclude_info={'hidden'})
    theads = [pi['key'] for pi in prop_info]
    return render_template('admin/view_table.html', table_names=DBModel.keys(), table_name=table_name, theads=theads, models=models, prop_info=prop_info, PageText=g.PageText)

def modify_record(table_name, record_id):
    if table_name not in DBModel:
        return jsonify({'status': 'error', 'message': 'Table not found'})
    Model = DBModel[table_name]

    if request.method == 'POST':
        form_data = request.form.to_dict()
        record_id = request.form.get('id')
        form_data.pop('id', None)
        form_data_original = form_data.copy();
        for key in form_data_original:
            if form_data_original[key] == '':
                form_data.pop(key, None)
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
                    'message': g.PageText['SuccessSavedChanges']
                })
            except Exception as e:
                sess.rollback()
                msg = g.PageText['FailedTo'] + ' ' + g.PageText['SaveChanges'].lower()
                err = g.PageText['ErrorIn']
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
        PageText=g.PageText, 
        table_name=table_name, 
        model=model,
        record_id=record_id,
        options_fk=options_fk, 
        prop_info=prop_info
    )

def delete_record(table_name, record_id):
    if table_name not in DBModel:
        return jsonify({'status': 'error', 'message': g.PageText['TableNotFound']})
 
    Model = DBModel[table_name]

    with db_session() as sess:
        model = sess.get(Model, record_id)
        if model:
            sess.delete(model)
            msg = json.dumps(model.data_dict(data_style='rel_name'))
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

def download_csv():
    data = request.get_json()
    columns = data.get('columns', [])
    table_name = request.args.get('table_name')
    if table_name not in DBModel:
        return 'Table not found', 404
    Model = DBModel[table_name]
    with db_session() as session:
        models = session.scalars(select(Model)).all()
    
    # Create CSV
    csv_data = []
    header = [Model.get_properties(data_style='rel_name')[int(col)] for col in columns]
    csv_data.append(header)
    for model in models:
        row = [getattr(model, Model.get_properties(data_style='rel_name')[int(col)]) for col in columns]
        csv_data.append(row)
    
    # Create response
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(csv_data)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=data.csv"
    output.headers["Content-type"] = "text/csv"
    return output
