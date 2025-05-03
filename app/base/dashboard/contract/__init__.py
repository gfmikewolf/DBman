# app/base/dashboard/contract/__init__.py
from flask import Blueprint
from .views import view_contracts, frame_gantt_charts
from .views import frame_gantt

dashboard_contract_bp = Blueprint(
    'contract', 
    __name__, 
    url_prefix='/contract'
)

dashboard_contract_bp.route('/view_contracts', methods=['GET'], defaults={'contract_id': None})(view_contracts)
dashboard_contract_bp.route('/view_contracts/<int:contract_id>', methods=['GET'])(view_contracts)
dashboard_contract_bp.route('/frame_gantt_charts', methods=['GET'])(frame_gantt_charts)
dashboard_contract_bp.route('/frame_gantt/<contract_id>', methods=['GET'])(frame_gantt)

Dashboards = {
    'View Contracts': '/dashboard/contract/view_contracts',
    'Frame Contract Gantt Charts': '/dashboard/contract/frame_gantt_charts'
}
