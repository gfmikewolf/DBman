# app/base/crud/__init__.py
from flask import Blueprint
from .views import index, view_table, modify_record, delete_record, view_record

crud_bp = Blueprint('crud', __name__, template_folder='templates', url_prefix='/crud')

crud_bp.route('/view_table/<table_name>', methods=['GET', 'POST'])(view_table)
crud_bp.route('/modify_record/<table_name>/<record_id>', methods=['GET', 'POST'])(modify_record)
crud_bp.route('/delete_record/<table_name>/<record_id>', methods=['DELETE'])(delete_record)
crud_bp.route('/', methods=['GET'])(index)
crud_bp.route('/view_record/<table_name>/<record_id>', methods=['GET'])(view_record)
