import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== 数据库 ====================
# Railway 部署：自动使用 PostgreSQL（如果有 DATABASE_URL 环境变量）
# 本地开发：使用 SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'worklog.db')

SQLALCHEMY_TRACK_MODIFICATIONS = False

# ==================== 安全 ====================
SECRET_KEY = os.environ.get("SECRET_KEY", "worklog-secret-key-2026-change-in-production")
JWT_EXPIRATION_HOURS = 72

# ==================== 服务器 ====================
# Railway 会自动设置 PORT 环境变量
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# ==================== 微信小程序 ====================
# 从微信公众平台获取
WECHAT_APPID = os.environ.get("WECHAT_APPID", "your_appid_here")
WECHAT_SECRET = os.environ.get("WECHAT_SECRET", "your_secret_here")

# ==================== 工作日配置 ====================
# 每天标准工时（小时）
STANDARD_HOURS_PER_DAY = 8.0

# 中国节假日 API (https://timor.tech/api/holiday)
HOLIDAY_API_URL = 'https://timor.tech/api/holiday/year/'