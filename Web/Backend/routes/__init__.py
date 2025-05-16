from flask import Blueprint

# 创建蓝图
electricity_bp = Blueprint('electricity', __name__)
history_bp = Blueprint('history', __name__)
debug_bp = Blueprint('debug', __name__)

# 导入路由
from . import electricity_routes
from . import history_routes
from . import debug_routes

def init_app(app):
    """初始化所有路由蓝图"""
    app.register_blueprint(electricity_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(debug_bp) 