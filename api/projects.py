"""项目管理接口"""
from flask import request, jsonify
from api import api_bp
from database import db
from models import Project, ProjectTask


@api_bp.route("/projects", methods=["GET"])
def list_projects():
    projects = Project.query.filter_by(is_active=True).order_by(Project.code).all()
    result = []
    for p in projects:
        tasks = ProjectTask.query.filter_by(project_id=p.id, is_active=True).order_by(ProjectTask.sort_order).all()
        result.append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "tasks": [{
                "id": t.id,
                "task_name": t.task_name,
            } for t in tasks]
        })
    return jsonify({"code": 0, "data": result})


@api_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json() or {}
    code = data.get("code", "").strip().upper()
    name = data.get("name", "").strip()
    tasks = data.get("tasks", [])  # ["筛选入组", "完成进度"]

    if not code or not name:
        return jsonify({"code": 400, "msg": "项目编号和名称不能为空"})
    if Project.query.filter_by(code=code).first():
        return jsonify({"code": 400, "msg": "项目编号已存在"})

    proj = Project(code=code, name=name)
    db.session.add(proj)
    db.session.flush()

    for i, task_name in enumerate(tasks):
        task_name = task_name.strip()
        if task_name:
            task = ProjectTask(project_id=proj.id, task_name=task_name, sort_order=i)
            db.session.add(task)

    db.session.commit()
    return jsonify({"code": 0, "msg": "创建成功", "data": {"id": proj.id}})


@api_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    proj = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    if "name" in data:
        proj.name = data["name"].strip()
    if "code" in data:
        proj.code = data["code"].strip().upper()
    if "tasks" in data:
        # 替换任务列表
        ProjectTask.query.filter_by(project_id=proj.id).delete()
        for i, task_name in enumerate(data["tasks"]):
            task_name = task_name.strip()
            if task_name:
                task = ProjectTask(project_id=proj.id, task_name=task_name, sort_order=i)
                db.session.add(task)
    db.session.commit()
    return jsonify({"code": 0, "msg": "更新成功"})


@api_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    proj = Project.query.get_or_404(project_id)
    proj.is_active = False
    db.session.commit()
    return jsonify({"code": 0, "msg": "已禁用"})
