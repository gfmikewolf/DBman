# app/base/__init__.py
from flask import Blueprint

from .crud import crud_bp
from .api import api_bp
from .views import index, set_lang

base_bp = Blueprint('base', __name__, template_folder='templates', static_folder='static', static_url_path='/base/static')

base_bp.route('/')(index)
base_bp.route('/set_lang/<lang>')(set_lang)

base_bp.register_blueprint(crud_bp)
base_bp.register_blueprint(api_bp)
