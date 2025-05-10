# app/base/auth/privilege.py
from typing import Iterable, Any
from functools import wraps
from flask import abort, session
from sqlalchemy import select

class Privilege:
    _admin_role = '_admin'
    _anonymous_role = '_anonymous'

    @classmethod
    def is_admin(cls) -> bool:
        return cls._admin_role in session.get('ROLE_FAMILY', set())
    
    def __init__(self, role_names: Iterable[str] | str = '_anonymous'):
        from app.extensions import db_session
        from app.database.user import UserRole
        self.table_privilege: dict[str, str] = dict()
        self.role_family: set[str] = set()
        with db_session() as sess:
            if isinstance(role_names, str):
                role_names = [role_names]
            user_roles = sess.scalars(
                select(UserRole)
                .where(UserRole.user_role_name.in_(role_names))
            ).all()
            self.role_family = set()
            for user_role in user_roles:
                self.role_family |= {ur.user_role_name for ur in user_role.role_family}

    @classmethod
    def session_match(cls, role_names: str | Iterable[str]) -> bool:
        role_family: set[str] = set(session.get('ROLE_FAMILY', set()))
        return cls.match(role_family, role_names)

    def self_match(self, role_names: str | Iterable[str]) -> bool:
        return self.match(self.role_family, role_names)
            
    @staticmethod
    def match(role_family: set[str], role_names: str | Iterable[str]) -> bool:
        if not role_names or Privilege._admin_role in role_family:
            return True
        elif not role_family:
            return False
        if isinstance(role_names, str):
            return role_names in role_family
        elif isinstance(role_names, Iterable):
            return bool(set(role_names) & role_family)
        return False

def require_privilege(role_names: str | Iterable[str]):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not all(k in session for k in ('ROLE_FAMILY', 'USER_NAME')):
                priv = Privilege('_anonymous')
                session['ROLE_FAMILY'] = list(priv.role_family)
                session['USER_NAME']   = '_anonymous'
            if not (
                # request.remote_addr == '127.0.0.1' or
                Privilege.session_match(role_names)
            ):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
