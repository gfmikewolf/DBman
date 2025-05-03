# app/__init__.py
from flask import Flask, session, render_template, current_app, redirect, url_for
from app.utils import _
from app.extensions import Cache, db_session

def create_app():

    app = Flask(__name__)  
    
    from config import Config
    app.config.from_object(Config)

    from app.base import base_bp
    app.register_blueprint(base_bp)

    app.jinja_env.globals["_"] = _

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.jinja'), 404
    @app.errorhandler(403)
    def auth_required(e):
        return redirect(url_for('base.auth.app_login'))
    @app.before_request
    def init_session():
        if not Cache.active:
            with db_session() as sess:
                Cache.init_caches(sess)
        if 'LANG' not in session:
            session['LANG'] = current_app.config['TRANSLATOR'].lang
    return app
