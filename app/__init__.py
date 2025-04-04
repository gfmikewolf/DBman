# app/__init__.py
from flask import Flask, abort, session, render_template
from app.translation import get_dbman_dict, get_lang, translate_text

def _(input_text: str, dbman_dict_name_list: list[str] | None = []) -> str:
    dbman_dict = dict()
    lang = get_lang()
    if not dbman_dict_name_list:
        dbman_dict = session['DBMan_dict'][lang]
    else:
        for name in dbman_dict_name_list:
            if lang not in session['DBMan_spec_dict']:
                session['DBMan_spec_dict'][lang] = dict()
            if name not in session['DBMan_spec_dict'][lang]:
                file_dict = get_dbman_dict([name])
                session['DBMan_spec_dict'][lang][name] = file_dict
                dbman_dict.update(file_dict)
            else:
                dbman_dict.update(session['DBMan_spec_dict'][lang][name])

    if dbman_dict:
        return translate_text(input_text, dbman_dict, lang)
    else:
        return input_text

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

    @app.before_request
    def before_request():
        if 'DBMan_dict' not in session:
            session['DBMan_dict'] = dict()
        if 'DBMan_spec_dict' not in session:
            session['DBMan_spec_dict'] = dict()
        lang = get_lang()
        session_dict = session['DBMan_dict'].get(lang, None)
        if not session_dict:
            file_dict = get_dbman_dict(Config.LOCALES)
            session['DBMan_dict'][lang] = file_dict

    return app
