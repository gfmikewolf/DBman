# app/base/auth/privilege.py
from typing import Iterable
from collections import deque
from functools import wraps
from flask import request, abort, session
from sqlalchemy import select

class Privilege:
    _admin_role = '_admin'
    
    @classmethod
    def is_admin(cls) -> bool:
        return cls._admin_role in session.get('ROLE_FAMILY', set())
    
    def __init__(self, role_names: Iterable[str] | str = '_anonymous'):
        from app.extensions import db_session
        from app.database.user import UserRole
        self.table_privilege: dict[str, str] = dict()
        self.role_family: set[str] = set()
        self.role_ids: set[int] = set()
        with db_session() as sess:
            if isinstance(role_names, str):
                role_names = [role_names]
            if self._admin_role in role_names:
                self.role_family = {self._admin_role}
                return
            user_roles = sess.scalars(
                select(UserRole)
                .where(UserRole.user_role_name.in_(role_names))
            ).all()
            for user_role in user_roles:
                dq = deque([user_role])
                if user_role.user_role_name == self._admin_role:
                    self.role_family = {self._admin_role}
                    return
                self.role_family.add(user_role.user_role_name)
                self.role_ids.add(user_role.user_role_id)
                for k, v in user_role.table_privilege.items():
                    if k in self.table_privilege:
                        self.table_privilege[k] = ''.join(
                            sorted({p for p in (v + self.table_privilege.get(k))})
                        )
                    else:
                        self.table_privilege[k] = v               
                while dq:
                    role = dq.popleft()
                    for parent in getattr(role, 'parents', []):
                        name = getattr(parent, 'user_role_name', None)
                        if name == self._admin_role:
                            self.role_family = {self._admin_role}
                            return
                        if name and name not in self.role_family:
                            self.role_family.add(name)
                            self.role_ids.add(parent.user_role_id)
                            dq.append(parent)

    @classmethod
    def session_match(cls, role_names: str | Iterable[str]) -> bool:
        role_family: set[str] = set(session.get('ROLE_FAMILY', set()))
        return cls.match(role_family, role_names)

    def self_match(self, role_names: str | Iterable[str]) -> bool:
        return self.match(self.role_family, role_names)
            
    @staticmethod
    def match(role_family: set[str], role_names: str | Iterable[str]) -> bool:
        if not role_names or Privilege._admin_role in role_names:
            return True
        elif not role_family:
            return False
        
        if isinstance(role_names, str):
            return role_names in role_family
        elif isinstance(role_names, Iterable):
            return bool(set(role_names) & role_family)
        return False

    @classmethod
    def get_session_role_ids(cls) -> set[int]:
        return set(session.get('ROLE_IDS', set()))
        
    def match_table(self, table_privilege: dict[str, str]) -> bool:
        for table, rw in table_privilege.items():
            if table not in self.table_privilege and '_all' not in self.table_privilege:
                return False
            if not rw:
                continue
            self_rw = self.table_privilege.get(table, None) or self.table_privilege.get('_all', '')
            if rw not in self_rw:
                return False
        return True


def require_privilege(role_names: str | Iterable[str]):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not all(k in session for k in ('ROLE_FAMILY', 'ROLE_IDS', 'USER_NAME')):
                priv = Privilege()
                session['ROLE_FAMILY'] = list(priv.role_family)
                session['ROLE_IDS']    = list(priv.role_ids)
                session['USER_NAME']   = '_anonymous'
            if not (
                request.remote_addr == '127.0.0.1' or
                Privilege.session_match(role_names)
            ):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
