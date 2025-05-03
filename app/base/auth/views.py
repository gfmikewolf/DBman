# app/base/auth/views.py
from flask import redirect, render_template, request, session, url_for
from app.extensions import db_session
from app.base.auth.privilege import Privilege

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
        db_user = sess.query(User).filter_by(user_name=user_name).first()
        if db_user and db_user.check_password(user_pw): # type: ignore
            priv = Privilege({ur.user_role_name for ur in db_user.user_roles})
            session['ROLE_IDS'] = list(priv.role_ids)
            session['ROLE_FAMILY'] = list(priv.role_family)
            session['USER_NAME'] = db_user.user_name
            return redirect(url_for('base.index'))
        else:
            return render_template('login.jinja', failed=True)    
    
