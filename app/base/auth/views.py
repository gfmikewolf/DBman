# app/base/auth/views.py
from flask import redirect, render_template, request, session, url_for
from sqlalchemy import select
from app.extensions import db_session

def app_login():
    if request.method == 'GET':
        return render_template('login.jinja')
    
    if request.method != 'POST':
        return redirect('/')

    # request.method == 'POST'
    user_name = request.form.get('user_name', None)
    user_pw = request.form.get('password', None)
    if not user_name or not user_pw:
        return render_template('login.jinja', failed=True)
    
    with db_session() as sess:
        from app.database.user import User
        user = sess.scalar(select(User).where(User.user_name==user_name))
        if user and user.check_password(user_pw):
            session['ROLE_FAMILY'] = [ur.user_role_name for ur in user.role_family]
            session['USER_NAME'] = user.user_name
            return redirect(request.referrer)
        else:
            return render_template('login.jinja', failed=True)
    
