# app/base/auth/__init__.py
from flask import Blueprint
from .views import app_login

auth_bp = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

auth_bp.route('/login', methods=['GET', 'POST'])(app_login)
