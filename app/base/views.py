# app/base/views.py
from flask import redirect, request, render_template, current_app, session
from app.base.dashboard import Dashboards
from app.utils.templates import PageNavigation

navigation = PageNavigation ({
    'Homepage': '#',
})

def index() -> str:
    return render_template(
        'index.jinja',
        dashboards=Dashboards, 
        navigation=navigation.index
    )

def set_lang(lang: str):
    if lang not in current_app.config['LANGSET']:
        raise ValueError(f'Lang: {lang} not in valid language set')
    session['LANG'] = lang
    return redirect(request.referrer)
