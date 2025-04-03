# api/translation/__init__.py
from flask import Blueprint

from .views import translate

translation_bp = Blueprint('datajson', __name__, url_prefix='/translate')

translation_bp.route('/<input_text>', methods=['GET'])(translate)
translation_bp.route('/spec/<spec_dict_names>/<input_text>', methods=['GET'])(translate)
