# app/admin_users_manager.py

from flask import Blueprint

admin_users_bp = Blueprint('admin_users', __name__, url_prefix='/api/admin-users')