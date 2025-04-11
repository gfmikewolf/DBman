from flask import current_app
from app.base.crud.utils import fetch_modify_form_viewer, fetch_instance
from app.extensions import db_session

def get_spec_form_entries(table_name: str) -> str:
    with db_session() as db_sess:
        instance = fetch_instance(table_name.lower(), '_new', db_sess)
        data = fetch_modify_form_viewer(instance, db_sess, True)
    template = current_app.jinja_env.get_template('macros/form-entries-dbman.jinja')
    
    return template.module.FormEntriesDBMan(data = data) # type: ignore
