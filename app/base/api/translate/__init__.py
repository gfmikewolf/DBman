# api/translation/__init__.py
from flask import Blueprint

from .views import translate

translate_bp = Blueprint('translate', __name__, url_prefix='/translate')

translate_bp.route('/<input_text>', methods=['GET'])(translate)
translate_bp.route('/spec/<spec_dict_names>/<input_text>', methods=['GET'])(translate)
