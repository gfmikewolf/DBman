# app/base/crud/views.py

# python
from enum import Enum
from hmac import new
from typing import Any
# flask
from flask import Response, render_template, request, jsonify, abort, url_for
# sqlalchemy
from sqlalchemy import delete, inspect
# app
from app import base
from app.database.utils import convert_value_by_python_type
from app.utils.templates import PageNavigation
from app.utils.common import _
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
        data=tabledata
    )

def modify_record(table_name: str, pks: str) -> Any:
    with db_session() as db_sess:
        instance = fetch_instance(table_name, pks, db_sess)
        polymorphic_key = instance.get_polymorphic_key()
        if request.method == 'GET':
            viewer_original = fetch_model_viewer(instance, db_sess)
            base_data, spec_data = fetch_modify_form_viewer(instance, db_sess)
            return render_template(
                'crud/modify_record.jinja',
                navigation = navigation.get_nav({'Modify record': '#'}), 
                table_name = table_name,
                polymorphic_key = polymorphic_key,
                data = base_data,
                spec_data = spec_data,
                pks = pks,
                viewer_original = viewer_original,
            )
        elif request.method == 'POST':
            form_data = request.get_json()
            if not form_data:
                return jsonify(success=False, error=_('No data provided')), 400
            if pks == '_new':
                instance = Base.get_obj(table_name, form_data)
                db_sess.add(instance)
            else:
                instance = fetch_instance(table_name, pks, db_sess)
                instance.update_data(form_data)
            try:
                db_sess.commit()
                return jsonify(success=True), 200
            except Exception as e:
                db_sess.rollback()
                return jsonify(success=False, error=str(e)), 500

def delete_record(table_name: str, pks: str) -> Response | tuple[Response, int]:
    if request.method != 'DELETE':
        abort(404)
    with db_session() as sess:
        instance = fetch_instance(table_name, pks, sess)
        try:
            sess.delete(instance)
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
        pks=pks,
        basic_info=basic_info,
        ref_objects=ref_objects,
        navigation=navigation.get_nav({
            'View table': url_for('base.crud.view_table', table_name=table_name),
            'View record': '#'
        })
    )
