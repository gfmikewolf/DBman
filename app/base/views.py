# app/base/views.py
from flask import redirect, request, render_template, current_app, session
from app.utils.templates import PageNavigation

# 本蓝图的基础导航
navigation = PageNavigation ({
    '_homepage': '#',
})

def index():
    return render_template('index.jinja', navigation=navigation.index)

def set_lang(lang: str):
    if lang not in current_app.config['LANGSET']:
        raise ValueError(f'Lang: {lang} not in valid language set')
    session['LANG'] = lang
    return redirect(request.referrer)
