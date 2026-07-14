"""工时记录系统 - Flask API 入口"""
import os
from datetime import date
from database import app, db
from models import init_db, WorkingDay
from api import api_bp

app.register_blueprint(api_bp)

# 启动时初始化数据库和节假日
with app.app_context():
    init_db()
    # 检查是否需要同步节假日
    year = date.today().year
    has_data = db.session.execute(
        db.select(WorkingDay).filter(
            WorkingDay.date >= f"{year}-01-01",
            WorkingDay.date <= f"{year}-12-31",
        ).limit(1)
    ).first()
    if not has_data:
        print(f"首次启动，同步 {year} 年节假日数据...")
        try:
            from utils.holiday import sync_holidays
            sync_holidays(year)
        except Exception as e:
            print(f"节假日同步失败: {e}（可稍后手动同步）")


@app.route("/")
def index():
    return {
        "name": "工时记录系统 API",
        "version": "1.0.0",
        "status": "running",
    }


if __name__ == "__main__":
    from config import HOST, PORT, DEBUG
    app.run(host=HOST, port=PORT, debug=DEBUG)
