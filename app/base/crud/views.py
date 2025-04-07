# app/base/crud/views.py

# python
from typing import Any
from weakref import ref
# flask
from flask import Response, render_template, request, jsonify, abort, url_for
# app
from config import Config
from app import _
from app.utils.templates import PageNavigation
from app.extensions import db_session, Base
from .utils import fetch_instance, fetch_model_viewer, fetch_modify_form_viewer, fetch_related_objects, fetch_tabledata, fetch_select_options

navigation = PageNavigation ({
    '_homepage': '/',
    '_crud': '/crud'
})
"""
navigation is a PageNavigation object that manages the navigation links for the CRUD views.
It contains links to the homepage and the CRUD index page.
"""

dbman_dict_name_list = Config.DATABASE_NAMES.split(',') # type: ignore
"""
db_dict is a list of database names, split by commas.
"""

def index() -> str:
    table_names = Base.model_map.keys()
    return render_template(
        'crud/index.jinja',  
        table_names=table_names, 
        navigation=navigation.index
    )

def view_table(table_name: str) -> str:
    if table_name not in Base.model_map:
        abort(404)
    Model = Base.model_map[table_name]
    with db_session() as db_sess:
        tabledata = fetch_tabledata(Model, db_sess)

    return render_template(
        'crud/view_table.jinja',
        navigation = navigation.get_nav({'View table': '#'}), 
        table_names=Base.model_map.keys(), 
        table_name=table_name,
        data=tabledata,
        dbman_dict_name_list=dbman_dict_name_list
    )

def modify_record(table_name: str, pks: str) -> Any:
    with db_session() as db_sess:
        instance = fetch_instance(table_name, pks, db_sess)
        if request.method == 'GET':
            viewer_original = fetch_model_viewer(instance, db_sess)
            data = fetch_modify_form_viewer(instance, db_sess)
            datajson_element_id_map = instance.get_col_datajson_id_map()
            return render_template(
                'crud/modify_record.jinja',
                navigation = navigation.get_nav({'Modify record': '#'}), 
                table_name = table_name, 
                pks = pks,
                data = data,
                viewer_original = viewer_original,
                datajson_element_id_map = datajson_element_id_map,
                dbman_dict_name_list = dbman_dict_name_list
            )
        elif request.method == 'POST':
            try:
                instance.update_data(request.get_json())
                if pks == '_new':
                    db_sess.add(instance)
                db_sess.commit()
                return jsonify(success=True), 200
            except Exception as e:
                db_sess.rollback()
                return jsonify(success=False, error=str(e)), 500
        else:
            abort(404)

def delete_record(table_name: str, pks: str) -> Response | tuple[Response, int]:
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
        
def view_record(table_name: str, pks: str) -> str:
    with db_session() as db_sess:
        model = fetch_instance(table_name, pks, db_sess)
        basic_info = fetch_model_viewer(model, db_sess)
        ref_objects = fetch_related_objects(model, db_sess)

    return render_template(
        'crud/view_record.jinja', 
        table_name=table_name,
        basic_info=basic_info,
        ref_objects=ref_objects,
        navigation=navigation.get_nav({
            'View table': url_for('base.crud.view_table', table_name=table_name),
            'View record': '#'
        })
    )