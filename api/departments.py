"""部门管理补充接口"""
from flask import request, jsonify
from api import api_bp
from database import db
from models import Department, User


@api_bp.route("/departments/<int:dept_id>", methods=["PUT"])
def update_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"code": 400, "msg": "部门名称不能为空"})
    if Department.query.filter(Department.name == name, Department.id != dept_id).first():
        return jsonify({"code": 400, "msg": "部门名称已存在"})
    dept.name = name
    db.session.commit()
    return jsonify({"code": 0, "msg": "更新成功"})


@api_bp.route("/departments/<int:dept_id>", methods=["DELETE"])
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    # 检查是否有人员关联
    user_count = User.query.filter_by(department_id=dept_id, is_active=True).count()
    if user_count > 0:
        return jsonify({"code": 400, "msg": f"该部门下还有 {user_count} 名活跃人员，无法删除"})
    dept.is_active = False
    db.session.commit()
    return jsonify({"code": 0, "msg": "已禁用"})
