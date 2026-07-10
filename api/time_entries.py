"""工时记录接口"""
from datetime import datetime, date
from flask import request, jsonify
from api import api_bp
from database import db
from models import User, Project, ProjectTask, TimeEntry, TimeEntryDetail, LeaveRecord


@api_bp.route("/time-entries", methods=["POST"])
def create_time_entry():
    """提交工时记录"""
    data = request.get_json() or {}
    user_id = data.get("user_id")
    project_id = data.get("project_id")
    record_date_str = data.get("record_date")  # "2026-07-09"
    tasks = data.get("tasks", [])  # [{task_id, progress, hours}]
    remark = data.get("remark", "")

    if not all([user_id, project_id, record_date_str]):
        return jsonify({"code": 400, "msg": "缺少必填字段"})

    try:
        record_date = date.fromisoformat(record_date_str)
    except ValueError:
        return jsonify({"code": 400, "msg": "日期格式错误"})

    # upsert: 存在则更新，不存在则创建
    entry = TimeEntry.query.filter_by(
        user_id=user_id, project_id=project_id, record_date=record_date
    ).first()

    if entry:
        # 删除旧的明细
        TimeEntryDetail.query.filter_by(entry_id=entry.id).delete()
    else:
        entry = TimeEntry(user_id=user_id, project_id=project_id, record_date=record_date)

    entry.remark = remark
    entry.updated_at = datetime.now()

    if not entry.id:
        db.session.add(entry)
    db.session.flush()

    # 添加明细
    total_hours = 0
    for t in tasks:
        task_id = t.get("task_id")
        progress = t.get("progress", "") or ""
        # 兼容旧数据：如果是数字转为字符串
        if isinstance(progress, (int, float)):
            progress = str(int(progress)) if progress == int(progress) else str(progress)
        hours = float(t.get("hours", 0))
        if task_id and hours > 0:
            detail = TimeEntryDetail(
                entry_id=entry.id,
                task_id=task_id,
                progress=progress,
                hours=hours,
            )
            db.session.add(detail)
            total_hours += hours

    db.session.commit()
    return jsonify({"code": 0, "msg": "保存成功", "data": {"id": entry.id, "total_hours": total_hours}})


@api_bp.route("/time-entries", methods=["GET"])
def query_time_entries():
    """查询工时记录"""
    user_id = request.args.get("user_id", type=int)
    project_id = request.args.get("project_id", type=int)
    record_date = request.args.get("date")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = TimeEntry.query

    if user_id:
        query = query.filter_by(user_id=user_id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    if record_date:
        try:
            d = date.fromisoformat(record_date)
            query = query.filter_by(record_date=d)
        except ValueError:
            pass
    if start_date:
        try:
            query = query.filter(TimeEntry.record_date >= date.fromisoformat(start_date))
        except ValueError:
            pass
    if end_date:
        try:
            query = query.filter(TimeEntry.record_date <= date.fromisoformat(end_date))
        except ValueError:
            pass

    entries = query.order_by(TimeEntry.record_date.desc(), TimeEntry.user_id).all()

    result = []
    for e in entries:
        details = []
        total_hours = 0
        for d in e.details:
            details.append({
                "task_id": d.task_id,
                "task_name": d.task.task_name if d.task else "",
                "progress": d.progress,
                "hours": d.hours,
            })
            total_hours += d.hours
        result.append({
            "id": e.id,
            "user_id": e.user_id,
            "user_name": e.user.name if e.user else "",
            "project_id": e.project_id,
            "project_code": e.project.code if e.project else "",
            "project_name": e.project.name if e.project else "",
            "record_date": e.record_date.isoformat(),
            "total_hours": round(total_hours, 1),
            "details": details,
            "remark": e.remark,
        })

    return jsonify({"code": 0, "data": result})


@api_bp.route("/time-entries/<int:entry_id>", methods=["DELETE"])
def delete_time_entry(entry_id):
    entry = TimeEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"code": 0, "msg": "已删除"})


@api_bp.route("/time-entries/today-status", methods=["GET"])
def today_status():
    """查询今日填写情况（首页用）"""
    today = date.today()
    users = User.query.filter_by(is_active=True).all()
    entries = TimeEntry.query.filter_by(record_date=today).all()
    submitted_user_ids = set(e.user_id for e in entries)
    leaves = LeaveRecord.query.filter_by(leave_date=today).all()
    leave_user_ids = set(l.user_id for l in leaves)

    result = []
    for u in users:
        status = "未填"
        if u.id in submitted_user_ids:
            status = "已填"
        elif u.id in leave_user_ids:
            status = "请假"
        result.append({
            "user_id": u.id,
            "user_name": u.name,
            "department_name": u.department.name if u.department else "",
            "status": status,
        })

    return jsonify({"code": 0, "data": result})
