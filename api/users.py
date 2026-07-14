"""人员管理接口"""
from flask import request, jsonify
from api import api_bp
from database import db
from models import User, Department


# ==================== 部门 ====================
@api_bp.route("/departments", methods=["GET"])
def list_departments():
    depts = Department.query.filter_by(is_active=True).order_by(Department.sort_order).all()
    return jsonify({
        "code": 0,
        "data": [{"id": d.id, "name": d.name} for d in depts]
    })


@api_bp.route("/departments", methods=["POST"])
def create_department():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"code": 400, "msg": "请输入部门名称"})
    if Department.query.filter_by(name=name).first():
        return jsonify({"code": 400, "msg": "部门已存在"})
    dept = Department(name=name)
    db.session.add(dept)
    db.session.commit()
    return jsonify({"code": 0, "data": {"id": dept.id, "name": dept.name}})


# ==================== 人员 ====================
@api_bp.route("/users", methods=["GET"])
def list_users():
    dept_id = request.args.get("department_id", type=int)
    query = User.query.filter_by(is_active=True)
    if dept_id:
        query = query.filter_by(department_id=dept_id)
    users = query.order_by(User.department_id, User.name).all()
    return jsonify({
        "code": 0,
        "data": [{
            "id": u.id,
            "name": u.name,
            "department_id": u.department_id,
            "department_name": u.department.name if u.department else "",
            "role": u.role,
        } for u in users]
    })


@api_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    dept_id = data.get("department_id")
    if not name:
        return jsonify({"code": 400, "msg": "请输入姓名"})
    user = User(name=name, department_id=dept_id)
    db.session.add(user)
    db.session.commit()
    return jsonify({"code": 0, "msg": "创建成功", "data": {"id": user.id}})


@api_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    if "name" in data:
        user.name = data["name"].strip()
    if "department_id" in data:
        user.department_id = data["department_id"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "role" in data and data["role"] in ("admin", "user"):
        user.role = data["role"]
    db.session.commit()
    return jsonify({"code": 0, "msg": "更新成功"})


@api_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return jsonify({"code": 0, "msg": "已禁用"})
