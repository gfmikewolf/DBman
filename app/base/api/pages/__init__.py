# app/api/pages/__init__.py

from flask import Blueprint
from .views import get_spec_form_entries

pages_bp = Blueprint('pages', __name__, url_prefix='/pages')

pages_bp.route(
    '/spec_form_entries/<table_name>', 
    methods=['GET'])(get_spec_form_entries)
