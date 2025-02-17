# app/base/__init__.py
from flask import Blueprint
from app.translation import set_language
from .admin import admin_bp
from .views import index

base_bp = Blueprint('base', __name__, template_folder='templates', static_folder='static', static_url_path='/base/static')

base_bp.route('/')(index)
base_bp.route('/lang/<lang>')(set_language)

base_bp.register_blueprint(admin_bp)