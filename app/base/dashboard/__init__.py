from flask import Blueprint
from .views import simple_viewer
from .contract import dashboard_contract_bp, Dashboards as Dashboards_contract

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
dashboard_bp.register_blueprint(dashboard_contract_bp)
dashboard_bp.route('/simple_viewer/<string:table_name>/<string:pks>')(simple_viewer)

Dashboards = {}

Dashboards.update(Dashboards_contract)
