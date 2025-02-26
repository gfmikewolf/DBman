# app/base/views.py
from flask import g, render_template

def index():
    return render_template('index.html', navigation={'Home':'#'}, PageText=g.PageText)