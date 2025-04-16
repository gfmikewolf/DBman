# app/base/auth/views.py
from flask import abort, redirect, render_template, request, session
from app.extensions import db_session, Base

def app_login():
    if request.method == 'GET':
        return render_template('login.jinja')
    
    if request.method != 'POST':
        return redirect('/')

    # request.method == 'POST'
    User = Base.model_map['user']
    user_name = request.form.get('user_name', None)
    user_pw = request.form.get('password', None)
    if not user_name or not user_pw:
        return render_template('login.jinja', failed=True)

    with db_session() as sess:
        db_user = sess.query(User).filter_by(user_name=user_name).first()
        merged_role = None
        if db_user and db_user.check_password(user_pw): # type: ignore
            merged_role = sum(db_user.user_roles[1:], db_user.user_roles[0]) # type: ignore
    if merged_role:
        session['_priv'] = merged_role.table_privilege # type: ignore
        session['user_name'] = db_user.user_name # type: ignore
        return redirect('/')
    else:
        return render_template('login.jinja', failed=True)    
    
