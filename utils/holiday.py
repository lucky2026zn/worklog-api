"""中国节假日工具 - 使用 timor.tech API"""
import json
import urllib.request
from datetime import date, timedelta
from database import db
from models import WorkingDay


def sync_holidays(year):
    """从 timor.tech API 同步指定年份的节假日数据"""
    url = f"https://timor.tech/api/holiday/year/{year}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"节假日 API 请求失败: {e}")
        print(f"使用内置节假日数据作为补充...")
        data = {"holiday": _get_builtin_holidays(year)}

    if data.get("code") != 0 and "holiday" not in data:
        print(f"API 返回异常，使用内置数据")
        data = {"holiday": _get_builtin_holidays(year)}

    holidays = data.get("holiday", {})

    # 清空该年份旧数据
    WorkingDay.query.filter(
        db.extract("year", WorkingDay.date) == year
    ).delete()

    # 首先生成全年默认数据（周末休息，工作日上班）
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    current = start
    while current <= end:
        is_weekend = current.weekday() >= 5  # 5=周六, 6=周日
        wd = WorkingDay(
            date=current,
            is_workday=not is_weekend,
            is_weekend=is_weekend,
            is_legal_holiday=False,
            holiday_name=None,
        )
        db.session.add(wd)
        current += timedelta(days=1)

    db.session.flush()

    # 然后应用节假日覆盖
    for date_str, info in holidays.items():
        if not info:
            continue
        try:
            d = date.fromisoformat(date_str)
        except ValueError:
            continue

        is_holiday = info.get("holiday", False)
        name = info.get("name", "")
        holiday_date = info.get("date", "")

        if isinstance(holiday_date, str) and holiday_date:
            try:
                d = date.fromisoformat(holiday_date)
            except ValueError:
                continue

        existing = WorkingDay.query.filter_by(date=d).first()
        if existing:
            existing.is_workday = not is_holiday
            existing.is_legal_holiday = is_holiday
            existing.holiday_name = name

    db.session.commit()
    print(f"已同步 {year} 年节假日数据")


def _get_builtin_holidays(year):
    """内置 2026 年节假日数据（备降方案）"""
    builtin = {
        2026: {
            # 元旦
            "2026-01-01": {"holiday": True, "name": "元旦"},
            "2026-01-02": {"holiday": True, "name": "元旦"},
            "2026-01-03": {"holiday": True, "name": "元旦"},
            # 春节
            "2026-02-15": {"holiday": True, "name": "春节"},
            "2026-02-16": {"holiday": True, "name": "春节"},
            "2026-02-17": {"holiday": True, "name": "春节"},
            "2026-02-18": {"holiday": True, "name": "春节"},
            "2026-02-19": {"holiday": True, "name": "春节"},
            "2026-02-20": {"holiday": True, "name": "春节"},
            "2026-02-21": {"holiday": True, "name": "春节"},
            # 清明
            "2026-04-04": {"holiday": True, "name": "清明节"},
            "2026-04-05": {"holiday": True, "name": "清明节"},
            "2026-04-06": {"holiday": True, "name": "清明节"},
            # 劳动节
            "2026-05-01": {"holiday": True, "name": "劳动节"},
            "2026-05-02": {"holiday": True, "name": "劳动节"},
            "2026-05-03": {"holiday": True, "name": "劳动节"},
            "2026-05-04": {"holiday": True, "name": "劳动节"},
            "2026-05-05": {"holiday": True, "name": "劳动节"},
            # 端午
            "2026-06-25": {"holiday": True, "name": "端午节"},
            "2026-06-26": {"holiday": True, "name": "端午节"},
            "2026-06-27": {"holiday": True, "name": "端午节"},
            # 中秋+国庆
            "2026-10-01": {"holiday": True, "name": "国庆节"},
            "2026-10-02": {"holiday": True, "name": "国庆节"},
            "2026-10-03": {"holiday": True, "name": "国庆节"},
            "2026-10-04": {"holiday": True, "name": "国庆节"},
            "2026-10-05": {"holiday": True, "name": "国庆节"},
            "2026-10-06": {"holiday": True, "name": "国庆节"},
            "2026-10-07": {"holiday": True, "name": "国庆节"},
            "2026-10-08": {"holiday": True, "name": "国庆节"},
        }
    }
    return builtin.get(year, {})


def get_workdays_count(year, month):
    """获取指定月份的工作日天数"""
    return WorkingDay.query.filter(
        db.extract("year", WorkingDay.date) == year,
        db.extract("month", WorkingDay.date) == month,
        WorkingDay.is_workday == True,
    ).count()


def get_working_hours(year, month):
    """获取指定月份的应出勤工时"""
    from config import STANDARD_HOURS_PER_DAY
    days = get_workdays_count(year, month)
    return days * STANDARD_HOURS_PER_DAY
