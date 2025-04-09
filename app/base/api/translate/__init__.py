# api/translate/__init__.py
from flask import Blueprint

from .views import translate_g, translate_s

translate_bp = Blueprint('translate', __name__, url_prefix='/translate')

translate_bp.route('/<input_text>', methods=['GET'])(translate_g)
translate_bp.route('/spec/<input_text>', methods=['GET'])(translate_s)
