"""API 蓝图初始化"""
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from . import auth, users, projects, departments, time_entries, reports, working_days, exports
