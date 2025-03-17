# app/base/views.py
from flask import render_template
from app.utils.templates import PageNavigation

# 本蓝图的基础导航
navigation = PageNavigation ({
    '_homepage': '#',
})

def index():
    return render_template('index.jinja', navigation=navigation.index)
