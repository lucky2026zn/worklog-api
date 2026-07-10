"""认证接口 - 支持首次登录自动注册"""
import hashlib
from datetime import datetime, timedelta
from flask import request, jsonify
from api import api_bp
from database import db
from models import User


@api_bp.route("/auth/login", methods=["POST"])
def login():
    """
    登录接口：
    - 用户已存在 → 直接登录成功
    - 用户不存在 → 自动创建（第一人自动设为管理员）
    """
    data = request.get_json() or {}
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"code": 400, "msg": "请输入姓名"})

    user = User.query.filter_by(name=name, is_active=True).first()

    if not user:
        # 自动创建新用户
        # 检查是否有已存在的用户，第一个注册的设为管理员
        existing_count = User.query.count()
        role = "admin" if existing_count == 0 else "user"

        user = User(name=name, role=role)
        db.session.add(user)
        db.session.commit()

        msg = "自动创建账号成功"
    else:
        msg = "登录成功"

    return jsonify({
        "code": 0,
        "msg": msg,
        "data": {
            "user_id": user.id,
            "name": user.name,
            "department_id": user.department_id,
            "department_name": user.department.name if user.department else "",
            "role": user.role,
            "token": _generate_token(user.id),
        }
    })


def _generate_token(user_id):
    """简化 token 生成"""
    raw = f"{user_id}:{datetime.now().timestamp()}:worklog-secret"
    return hashlib.md5(raw.encode()).hexdigest()
