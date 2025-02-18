# app/base/admin/views.py
import io
import csv
from flask import g, render_template, session, request, make_response
from sqlalchemy import select
from app.extensions import db_session, DBModel, ForeignKeyMixin

def admin_index():
    table_names = DBModel.keys()
    return render_template('admin/index.html', PageText=g.PageText, table_names=table_names)

def view_table(table_name):
    """查看表数据"""
    if table_name not in DBModel:
        return 'Table not found', 404
    Model = DBModel[table_name]
    with db_session() as session:
        models = session.scalars(select(Model)).all()
    theads = Model.get_properties(data_style='rel_name', exclude_info={'hidden'})
    return render_template('admin/view_table.html', table_names=DBModel.keys(), table_name=table_name, theads=theads, models=models, PageText=g.PageText)

def modify_record(table_name, item_id):
    if table_name not in DBModel:
        return 'Table not found', 404
    Model = DBModel[table_name]
   
    mod_props = Model.get_properties(exclude_info={'readonly'})
    
    with db_session() as sess:
        options_fk = {}
        if issubclass(Model, ForeignKeyMixin):
            options_fk = Model.get_options_fk(sess)
        model = session.scalar(select(Model))
    return render_template('admin/modify_item.html', PageText=g.PageText, table_name=table_name, model=model, mod_props=mod_props)

def delete_record(table_name, item_id):
    table_names = DBModel.keys()
    return render_template('admin/view_table.html', PageText=g.PageText, table_names=table_names)

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
