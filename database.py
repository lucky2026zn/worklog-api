from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, DEBUG

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SECRET_KEY"] = SECRET_KEY
app.config["DEBUG"] = DEBUG
app.config["JSON_AS_ASCII"] = False  # 支持中文

# PostgreSQL 兼容设置
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,       # 连接前检查，防止连接池断开
    "pool_recycle": 300,         # 300 秒回收连接
}

CORS(app)
db = SQLAlchemy(app)