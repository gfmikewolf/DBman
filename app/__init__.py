# app/__init__.py
from flask import Flask, g, abort, request
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
        current_bp = request.blueprint
        bp_name = request.blueprint.removeprefix('base.').lower() if current_bp else 'admin'
        locale_names = ['locale']
        if set([bp_name]).issubset(set(map(str.lower, Config.LOCALES))):
            locale_names = locale_names + [bp_name]
        g.PageText = get_pagetext(locale_names)
        if not g.PageText:
            # 如果翻译文件读取失败，返回错误信息
            print(f'Fail to load pagetext. {locale_names}')
            abort(404)

    return app
