# app/__init__.py
import os
from flask import Flask, g, abort
from app.extensions import db_session, DBModel
from app.translation import get_pagetext



def create_app():
    app = Flask(__name__)
    
    from config import Config
    app.config.from_object(Config)

    # 注册蓝图
    from app.base import base_bp
    app.register_blueprint(base_bp)

    # 请求前确认翻译文件正确读取
    @app.before_request
    def before_request():
        BASE_DIR = os.path.join(os.getcwd(), 'app', 'base')
        g.PageText = get_pagetext(BASE_DIR, 'locale')
        if not g.PageText:
        # 如果翻译文件读取失败，返回错误信息    
            abort(404)

    return app