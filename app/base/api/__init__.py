# app/base/api/__init.__py

from flask import Blueprint

# from .datajson import datajson_bp
from .translate import translate_bp
from .pages import pages_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')

# api_bp.register_blueprint(datajson_bp)
api_bp.register_blueprint(translate_bp)
api_bp.register_blueprint(pages_bp)
