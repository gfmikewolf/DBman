import bcrypt
from sqlalchemy import ForeignKey
from sqlalchemy.types import (
    Integer, JSON
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column, relationship, synonym
)
from ..base import Base

class User(Base):
    __tablename__ = 'user'
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_password_hash: Mapped[str] = mapped_column(info={'password': True})
    user_name: Mapped[str]
    
    user_roles: Mapped[list['UserRole']] = relationship(
        back_populates='users',
        secondary=lambda: UserMAPUserRole.__table__,
        lazy='select'
    )
    
    _name = synonym('user_name')
    
    @property
    def user_password(self):
        return None
    
    @user_password.setter
    def user_password(self, pw: str):
        self.user_password_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode(), self.user_password_hash.encode())

    key_info = {
        'data': (
            'user_id',
            'user_name',
            'user_password',
            'user_roles',
            'user_password_hash'
        ),
        'hidden': {
            'user_id',
            'user_password',
            'user_password_hash'
        },
        'readonly': {
            'user_id',
            'user_roles',
            'user_password_hash'
        },
        'password': { 'user_password' }
    }
class UserRole(Base):
    __tablename__ = 'user_role'
    user_role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_role_name: Mapped[str]
    table_privilege: Mapped[dict] = mapped_column(JSON)
    
    users: Mapped[list['User']] = relationship(
        back_populates='user_roles',
        secondary=lambda: UserMAPUserRole.__table__,
        lazy='select'
    )

    def __add__(self, other: 'UserRole') -> 'UserRole':
        if not isinstance(other, UserRole):
            return NotImplemented
        merged_priv = self.table_privilege or {}
        for k, v in (other.table_privilege or {}).items():
            if k in merged_priv:
                merged_priv[k] = ''.join(sorted(set(merged_priv[k]) | set(v)))
            else:
                merged_priv[k] = v
        merged = UserRole(user_role_name=f'{self.user_role_name}+{other.user_role_name}')
        merged.table_privilege = merged_priv
        return merged
    
    key_info = {
        'data': (
            'user_role_id',
            'user_role_name',
            'table_privilege',
            'users'
        ),
        'hidden': {
            'user_role_id'
        },
        'readonly': {
            'user_role_id',
            'users'
        }
    }
class UserMAPUserRole(Base):
    """
    .. example::
    ```python
    table_privilege = {'contract': 'ramd', ...}
    # r: read
    # w: write
    ```
    """
    __tablename__ = 'user__map__user_role'
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'), primary_key=True)
    user_role_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_role.user_role_id'), primary_key=True)
    user: Mapped['User'] = relationship(lazy='selectin', overlaps='users, user_roles')
    user_role: Mapped['UserRole'] = relationship(lazy='selectin', overlaps='users, user_roles')

    key_info = {
        'data': (
            'user_id',
            'user_role_id',
            'user',
            'user_role'
        ),
        'hidden': {
            'user_id',
            'user_role_id'
        },
        'readonly': {
            'user',
            'user_role'
        }
    }
