# app/base/crud/views.py

# python
from typing import Any
# flask
from flask import (
    Response, current_app, render_template, request, jsonify, abort, url_for
)
# sqlalchemy
# app
from app.utils.templates import PageNavigation
from app.utils.common import _
from app.extensions import db_session, Base, table_map
from app.base.auth.privilege import require_privilege
from .utils import (
    fetch_instance, 
    fetch_model_viewer, 
    fetch_modify_form_viewer, 
    fetch_related_objects, 
    fetch_tabledata,
    fetch_related_funcs
)

navigation = PageNavigation ({
    'Homepage': '/',
    'Database CRUD': '/crud'
})
"""
navigation is a PageNavigation object that manages the navigation links for the CRUD views.
It contains links to the homepage and the CRUD index page.
"""
@require_privilege('_anonymous')
def index() -> str:
    return render_template(
        'crud/index.jinja',  
        table_map=table_map, 
        navigation=navigation.index
    )

@require_privilege('viewer')
def view_table(table_name: str) -> str:
    if table_name not in Base.model_map:
        abort(404)
    Model = Base.model_map[table_name]
    with db_session() as db_sess:
        tabledata = fetch_tabledata(Model, db_sess)
        related_funcs = fetch_related_funcs(table_name, db_sess, 'class')
    db_table_funcs = {}
    for func, func_info in Base.func_map.get(table_name, {}).items():
        if func_info['func_type'] == 'class':
            db_table_funcs[func] = func_info
        

    return render_template(
        'crud/view_table.jinja',
        navigation = navigation.get_nav({'View table': '#'}), 
        table_map=table_map, 
        table_name=table_name,
        data=tabledata,
        related_funcs=related_funcs,
        db_table_funcs=db_table_funcs
    )

@require_privilege('db_admin')
def modify_record(table_name: str, pks: str) -> Any:
    with db_session() as db_sess:
        instance = fetch_instance(table_name, pks, db_sess)
        polymorphic_key = instance.get_polymorphic_key()
        if request.method == 'GET':
            initial_data = request.args.to_dict()
            viewer_original = fetch_model_viewer(instance, db_sess) if pks != '_new' else {}
            base_data, spec_data = fetch_modify_form_viewer(instance, db_sess, initial_data)
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
            form_data = request.form
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

@require_privilege('db_admin')
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

@require_privilege('_anonymous')        
def view_record(table_name: str, pks: str) -> str:
    with db_session() as db_sess:
        model = fetch_instance(table_name, pks, db_sess)
        basic_info = fetch_model_viewer(model, db_sess)
        related_objects = fetch_related_objects(model, db_sess)
        related_funcs = fetch_related_funcs(table_name, db_sess, 'instance')
    return render_template(
        'crud/view_record.jinja', 
        table_name=table_name,
        pks=pks,
        basic_info=basic_info,
        related_objects=related_objects,
        related_funcs=related_funcs,
        navigation=navigation.get_nav({
            'View table': url_for('base.crud.view_table', table_name=table_name),
            'View record': '#'
        })
    )

@require_privilege('db_admin')
def db_func(table_name: str, func_name: str) -> Response | tuple[Response, int]:
    if not (table_name in Base.model_map and func_name in Base.func_map[table_name]):
        abort(404)
    func_info = Base.func_map[table_name][func_name]
    if request.method == 'GET' and func_info['input_types']:
        # need to post parameters but the method is GET
        return jsonify(success=False, error=_('Invalid request method')), 400
    result = None
    files = dict()
    
    for param, param_type_required in func_info['input_types'].items():
        if param_type_required[0] == 'file':
            if param in request.files:
                files[param] = request.files[param]
        elif param_type_required[0] == 'file-multiple':
            files[param] = request.files.getlist(param)
        if param_type_required[1] and (param not in request.form and param not in request.files):
            return jsonify(success=False, error=_(f'Missing required parameter: {param}')), 400

    if func_info['func_type'] == 'instance':
        pks = request.form.get('_pks')
        if pks:
            with db_session() as db_sess:
                instance = fetch_instance(table_name, pks, db_sess)
                if instance:
                    result = getattr(instance, func_name)(
                        db_session=db_sess, 
                        **request.form.to_dict(), 
                        **files
                    )
    elif func_info['func_type'] == 'class':
        with db_session() as db_sess:
            result = getattr(Base.model_map[table_name], func_name)(
                db_session=db_sess, 
                **request.form.to_dict(), 
                **files
            )
    if not isinstance(result, dict):
        return jsonify(success=False, error=_('Invalid function result')), 500
    if not result['success']:
        return jsonify(success=False, error=result['error']), 500
    data = ''
    if 'data' in result:
        result_data = result['data']
        if isinstance(data, dict):
            result_data = {_(k, True): v for k, v in data.items()}
            template = current_app.jinja_env.get_template('macros/datadict-dbman.jinja')
            data = template.module.DatadictDBMan(data = result_data) # type: ignore
        elif isinstance(data, list):
            data = ''.join([f'<li>{item}</li>' for item in result_data])
        else:
            data = str(result_data)
    return jsonify(success=True, data=data), 200
