"""工作日历 & 请假接口"""
from datetime import date, datetime
from flask import request, jsonify
from api import api_bp
from database import db
from models import WorkingDay, LeaveRecord, User
from utils.holiday import sync_holidays, get_workdays_count


# ==================== 工作日历 ====================
@api_bp.route("/working-days/sync", methods=["POST"])
def sync_working_days():
    """同步指定年份的节假日"""
    data = request.get_json() or {}
    year = data.get("year") or date.today().year
    sync_holidays(int(year))
    return jsonify({"code": 0, "msg": f"{year}年节假日同步完成"})


@api_bp.route("/working-days", methods=["GET"])
def get_working_days():
    """获取指定月份的日历"""
    year = request.args.get("year", type=int) or date.today().year
    month = request.args.get("month", type=int) or date.today().month

    days = WorkingDay.query.filter(
        db.extract("year", WorkingDay.date) == year,
        db.extract("month", WorkingDay.date) == month,
    ).order_by(WorkingDay.date).all()

    return jsonify({
        "code": 0,
        "data": {
            "year": year,
            "month": month,
            "work_days_count": get_workdays_count(year, month),
            "days": [{
                "date": d.date.isoformat(),
                "is_workday": d.is_workday,
                "holiday_name": d.holiday_name,
                "is_weekend": d.is_weekend,
            } for d in days]
        }
    })


# ==================== 请假 ====================
@api_bp.route("/leaves", methods=["POST"])
def create_leave():
    """提交请假"""
    data = request.get_json() or {}
    user_id = data.get("user_id")
    leave_date_str = data.get("leave_date")
    leave_type = data.get("leave_type", "事假")
    duration_hours = data.get("duration_hours", 8.0)
    remark = data.get("remark", "")

    if not all([user_id, leave_date_str]):
        return jsonify({"code": 400, "msg": "缺少必填字段"})

    try:
        leave_date = date.fromisoformat(leave_date_str)
    except ValueError:
        return jsonify({"code": 400, "msg": "日期格式错误"})

    # upsert
    record = LeaveRecord.query.filter_by(user_id=user_id, leave_date=leave_date).first()
    if record:
        record.leave_type = leave_type
        record.duration_hours = duration_hours
        record.remark = remark
    else:
        record = LeaveRecord(user_id=user_id, leave_date=leave_date, leave_type=leave_type, duration_hours=duration_hours, remark=remark)
        db.session.add(record)

    db.session.commit()
    return jsonify({"code": 0, "msg": "请假已记录"})


@api_bp.route("/leaves", methods=["GET"])
def query_leaves():
    """查询请假记录"""
    user_id = request.args.get("user_id", type=int)
    year = request.args.get("year", type=int) or date.today().year
    month = request.args.get("month", type=int) or date.today().month

    query = LeaveRecord.query.filter(
        db.extract("year", LeaveRecord.leave_date) == year,
        db.extract("month", LeaveRecord.leave_date) == month,
    )
    if user_id:
        query = query.filter_by(user_id=user_id)

    records = query.order_by(LeaveRecord.leave_date).all()
    return jsonify({
        "code": 0,
        "data": [{
            "id": r.id,
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else "",
            "leave_date": r.leave_date.isoformat(),
            "leave_type": r.leave_type,
            "duration_hours": r.duration_hours,
            "remark": r.remark,
        } for r in records]
    })


@api_bp.route("/leaves/<int:leave_id>", methods=["DELETE"])
def delete_leave(leave_id):
    record = LeaveRecord.query.get_or_404(leave_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({"code": 0, "msg": "已删除"})
