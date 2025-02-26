# app/__init__.py
from flask import Flask, abort, session
from app.translation import get_pagetext



def create_app():
    app = Flask(__name__)
    
    from config import Config
    app.config.from_object(Config)

    # 注册蓝图
    from app.base import base_bp
    app.register_blueprint(base_bp)

    # 请求前确认翻译文件正确读取
    PageText = get_pagetext(Config.LOCALES)
    if not PageText:
        # 如果翻译文件读取失败，返回错误信息
        print(f'Fail to load pagetext. {Config.LOCALES}')
        abort(404)
    else:
        session['PageText'] = PageText

    return app
