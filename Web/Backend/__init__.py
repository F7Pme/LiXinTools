from flask import Flask, render_template

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__, 
                static_folder='../Frontend/static', 
                template_folder='../Frontend')
    
    # 注册首页路由
    @app.route('/')
    def index():
        """渲染主页"""
        return render_template('index.html')
    
    # 注册API路由
    from .routes import init_app as init_routes
    init_routes(app)
    
    return app 