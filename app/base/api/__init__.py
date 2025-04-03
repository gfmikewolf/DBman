# app/base/api/__init.__py

from flask import Blueprint

from app import _
from .datajson import datajson_bp
from .translation import translation_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')

api_bp.register_blueprint(datajson_bp)
api_bp.register_blueprint(translation_bp)
