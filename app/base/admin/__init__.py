# app/base/admin/__init__.py
from flask import Blueprint
from .views import admin_index, view_table, modify_record, delete_record, download_csv

admin_bp = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')

admin_bp.route('/view_table/<table_name>', methods=['GET', 'POST'])(view_table)
admin_bp.route('/modify_record/<table_name>/<item_id>', methods=['GET', 'POST'])(modify_record)
admin_bp.route('/delete_record/<table_name>/<item_id>', methods=['POST'])(delete_record)
admin_bp.route('/download_csv', methods=['POST'])(download_csv)
admin_bp.route('/', methods=['GET'])(admin_index)