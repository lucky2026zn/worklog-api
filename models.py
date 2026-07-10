from datetime import datetime, date
from database import db


# ==================== 部门/中心 ====================
class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    users = db.relationship("User", backref="department", lazy=True)


# ==================== 人员 ====================
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    wechat_openid = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    role = db.Column(db.String(20), default="user")  # admin / user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    time_entries = db.relationship("TimeEntry", backref="user", lazy=True)
    leave_records = db.relationship("LeaveRecord", backref="user", lazy=True)


# ==================== 项目 ====================
class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)  # 项目缩写
    name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    tasks = db.relationship("ProjectTask", backref="project", lazy=True, cascade="all,delete")


# ==================== 项目任务模板 ====================
class ProjectTask(db.Model):
    __tablename__ = "project_tasks"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    task_name = db.Column(db.String(100), nullable=False)  # 如"筛选入组"、"完成进度"
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


# ==================== 工时记录（主表，每人每天每个项目一条）====================
class TimeEntry(db.Model):
    __tablename__ = "time_entries"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    remark = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("user_id", "project_id", "record_date", name="uq_user_project_date"),
    )

    details = db.relationship("TimeEntryDetail", backref="entry", lazy=True, cascade="all,delete")
    project = db.relationship("Project", lazy=True)


# ==================== 工时明细（每个任务一行）====================
class TimeEntryDetail(db.Model):
    __tablename__ = "time_entry_details"
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey("time_entries.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("project_tasks.id"), nullable=False)
    progress = db.Column(db.String(200), default='')  # 进度说明，如"入组3例"、"访视2例"
    hours = db.Column(db.Float, default=0)     # 使用工时
    task = db.relationship("ProjectTask", lazy=True)


# ==================== 请假记录 ====================
class LeaveRecord(db.Model):
    __tablename__ = "leave_records"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    leave_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(50), default="事假")  # 事假/病假/年假/调休
    remark = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("user_id", "leave_date", name="uq_user_leave_date"),
    )


# ==================== 工作日历 ====================
class WorkingDay(db.Model):
    __tablename__ = "working_days"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    is_workday = db.Column(db.Boolean, nullable=False)  # True=上班, False=休息
    holiday_name = db.Column(db.String(100))  # 节假日名称
    is_legal_holiday = db.Column(db.Boolean, default=False)  # 是否法定节假日
    is_weekend = db.Column(db.Boolean, default=False)  # 是否周末


def init_db():
    from database import app
    with app.app_context():
        db.create_all()
        print("数据库初始化完成")
