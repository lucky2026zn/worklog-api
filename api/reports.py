"""日报/月报接口"""
from datetime import date
from flask import request, jsonify
from api import api_bp
from database import db
from models import User, Project, TimeEntry, TimeEntryDetail, LeaveRecord
from utils.holiday import get_workdays_count, get_working_hours
from config import STANDARD_HOURS_PER_DAY


@api_bp.route("/reports/daily", methods=["GET"])
def daily_report():
    """日报：某天每人每个项目的工时汇总"""
    report_date_str = request.args.get("date") or date.today().isoformat()
    try:
        report_date = date.fromisoformat(report_date_str)
    except ValueError:
        return jsonify({"code": 400, "msg": "日期格式错误"})

    users = User.query.filter_by(is_active=True).order_by(User.department_id, User.name).all()
    projects = Project.query.filter_by(is_active=True).order_by(Project.code).all()

    result = []
    for u in users:
        for p in projects:
            entry = TimeEntry.query.filter_by(
                user_id=u.id, project_id=p.id, record_date=report_date
            ).first()
            if entry:
                details = []
                total_hours = 0
                for d in entry.details:
                    details.append({
                        "task_name": d.task.task_name if d.task else "",
                        "progress": d.progress,
                        "hours": d.hours,
                    })
                    total_hours += d.hours
                result.append({
                    "user_id": u.id,
                    "user_name": u.name,
                    "department_name": u.department.name if u.department else "",
                    "project_code": p.code,
                    "project_name": p.name,
                    "total_hours": round(total_hours, 1),
                    "details": details,
                    "remark": entry.remark,
                    "is_leave": False,
                })

    # 请假的人
    leaves = LeaveRecord.query.filter_by(leave_date=report_date).all()
    leave_user_ids = set(l.user_id for l in leaves)

    for u in users:
        if u.id in leave_user_ids and not any(r["user_id"] == u.id for r in result):
            result.append({
                "user_id": u.id,
                "user_name": u.name,
                "department_name": u.department.name if u.department else "",
                "project_code": "",
                "project_name": "请假",
                "total_hours": 0,
                "details": [],
                "remark": "请假",
                "is_leave": True,
            })

    return jsonify({"code": 0, "data": {"date": report_date_str, "records": result}})


@api_bp.route("/reports/monthly", methods=["GET"])
def monthly_report():
    """月报：某人某月的项目工时汇总 + 工作百分比"""
    year = request.args.get("year", type=int) or date.today().year
    month = request.args.get("month", type=int) or date.today().month
    user_id = request.args.get("user_id", type=int)

    query = TimeEntry.query.filter(
        db.extract("year", TimeEntry.record_date) == year,
        db.extract("month", TimeEntry.record_date) == month,
    )
    if user_id:
        query = query.filter_by(user_id=user_id)

    entries = query.order_by(TimeEntry.user_id, TimeEntry.project_id).all()

    # 按用户+项目汇总
    summary = {}  # { (user_id, project_id): total_hours }
    for e in entries:
        key = (e.user_id, e.project_id)
        total = sum(d.hours for d in e.details)
        summary[key] = summary.get(key, 0) + total

    users_data = User.query.filter_by(is_active=True).all() if not user_id else [User.query.get(user_id)]
    users_data = [u for u in users_data if u]

    # 计算工作日
    work_days = get_workdays_count(year, month)
    standard_hours = work_days * STANDARD_HOURS_PER_DAY

    result = []
    for u in users_data:
        # 请假天数
        leave_days = LeaveRecord.query.filter(
            LeaveRecord.user_id == u.id,
            db.extract("year", LeaveRecord.leave_date) == year,
            db.extract("month", LeaveRecord.leave_date) == month,
        ).count()

        user_work_days = work_days - leave_days
        user_standard_hours = user_work_days * STANDARD_HOURS_PER_DAY

        # 项目工时
        project_hours = []
        total_hours = 0
        for (uid, pid), hours in summary.items():
            if uid == u.id:
                p = Project.query.get(pid)
                project_hours.append({
                    "project_code": p.code if p else "",
                    "project_name": p.name if p else "",
                    "total_hours": round(hours, 1),
                })
                total_hours += hours

        # 工作百分比
        percentage = round((total_hours / user_standard_hours * 100), 1) if user_standard_hours > 0 else 0

        result.append({
            "user_id": u.id,
            "user_name": u.name,
            "department_name": u.department.name if u.department else "",
            "project_hours": sorted(project_hours, key=lambda x: x["project_code"]),
            "total_hours": round(total_hours, 1),
            "work_days": work_days,
            "leave_days": leave_days,
            "actual_work_days": user_work_days,
            "standard_hours": user_standard_hours,
            "percentage": percentage,
        })

    return jsonify({
        "code": 0,
        "data": {
            "year": year,
            "month": month,
            "work_days": work_days,
            "records": result,
        }
    })
