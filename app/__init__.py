# app/__init__.py
from flask import Flask, session, render_template, current_app
from app.utils.common import _
from app.extensions import Base, db_session
from app.base.auth.privilege import Privilege

def create_app():

    app = Flask(__name__)  
    
    from config import Config
    app.config.from_object(Config)

    from app.base import base_bp
    app.register_blueprint(base_bp)

    app.jinja_env.globals["_"] = _

    app.config['_PRIV'] = Privilege()

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.jinja'), 404

    @app.before_request
    def init_session():
        if 'LANG' not in session:
            session['LANG'] = current_app.config['TRANSLATOR'].lang
    return app
