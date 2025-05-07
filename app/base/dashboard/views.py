from flask import render_template
from app.base.auth.privilege import require_privilege
from app.base.crud.utils import fetch_instance, fetch_model_viewer, fetch_related_objects, fetch_viewable_value, get_viewable_instance, get_viewable_instance_name
from app.database import db_session

_default_viewer = 'base.dashboard.simple_viewer'
@require_privilege('viewer')
def simple_viewer(table_name: str, pks: str) -> str:
    with db_session() as sess:
        instance = fetch_instance(table_name, pks, sess)
        name = get_viewable_instance_name(instance)
        description = fetch_viewable_value(instance, 'description', sess, _default_viewer) if hasattr(instance, 'description') else '' # type: ignore
        entries = fetch_model_viewer(instance, sess, viewer=_default_viewer)
        related_objects = fetch_related_objects(instance, sess, viewer=_default_viewer)
    return render_template(
        'dashboard/simple-viewer.jinja', 
        name=name,
        description=description,
        entries=entries,
        related_objects=related_objects
    )
