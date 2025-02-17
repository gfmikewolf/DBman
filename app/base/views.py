# app/base/views.py
import os
import json
from flask import g, render_template, session, url_for
from app.extensions import db_session, DBModel
from app.translation import get_pagetext

BASE_DIR = os.path.join(os.getcwd(), 'app', 'base')

def index():
    return render_template('index.html', PageText=g.PageText)