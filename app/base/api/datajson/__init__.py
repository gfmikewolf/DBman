# app/api/datajson/__init__.py

from flask import Blueprint
from .views import get_datajson_structure

datajson_bp = Blueprint('datajson', __name__, url_prefix='/datajson')

datajson_bp.route(
    '/structure/<datajson_id>', 
    methods=['GET'])(get_datajson_structure)
