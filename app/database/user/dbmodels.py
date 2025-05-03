import bcrypt
from sqlalchemy import ForeignKey
from sqlalchemy.types import (
    Integer, JSON
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column, relationship
)
from ..base import Base

class User(Base):
    __tablename__ = 'user'
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_password_hash: Mapped[str]
    user_name: Mapped[str]

    user_roles: Mapped[list['UserRole']] = relationship(
        back_populates='users',
        secondary=lambda: UserMAPUserRole.__table__,
        lazy='select'
    )
    
    def __str__(self) -> str:
        return self.user_name
    
    @property
    def user_password(self):
        return None
    
    @user_password.setter
    def user_password(self, pw: str):
        self.user_password_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode(), self.user_password_hash.encode())

    key_info = {
        'data': [
            'user_name',
            'user_password',
            'user_roles'
        ],
        'hidden': {
            'user_password'
        },
        'readonly': {
            'user_roles'
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

    parents: Mapped[list['UserRole']] = relationship(
        back_populates='children',
        secondary=lambda: UserRoleMAPUserRole.__table__,
        primaryjoin=lambda: UserRole.user_role_id == UserRoleMAPUserRole.child_id,
        secondaryjoin=lambda: UserRole.user_role_id == UserRoleMAPUserRole.parent_id,
        lazy='select'
    )
    children: Mapped[list['UserRole']] = relationship(
        back_populates='parents',
        secondary=lambda: UserRoleMAPUserRole.__table__,
        primaryjoin=lambda: UserRole.user_role_id == UserRoleMAPUserRole.parent_id,
        secondaryjoin=lambda: UserRole.user_role_id == UserRoleMAPUserRole.child_id,
        lazy='select'
    )
    def __str__(self) -> str:
        return self.user_role_name
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
        'data': [
            'user_role_name',
            'table_privilege',
            'users'
        ],
        'readonly': {
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
    def __str__(self) -> str:
        return f'{self.user} ∈ {self.user_role}'
    key_info = {
        'data': [
            'user_id',
            'user_role_id',
            'user',
            'user_role'
        ],
        'hidden': {
            'user_id',
            'user_role_id'
        },
        'readonly': {
            'user',
            'user_role'
        }
    }
class UserRoleMAPUserRole(Base):
    __tablename__ = 'user_role__map__user_role'
    child_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_role.user_role_id'), primary_key=True)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_role.user_role_id'), primary_key=True)
    child: Mapped['UserRole'] = relationship(
        foreign_keys=[child_id], 
        lazy='selectin', 
        overlaps='parents, children'
    )
    parent: Mapped['UserRole'] = relationship(
        foreign_keys=[parent_id], 
        lazy='selectin', 
        overlaps='children, parents'
    )
    def __str__(self) -> str:
        return f'{self.child} ∈ {self.parent}'

    key_info = {
        'data': [
            'child_id',
            'parent_id',
            'child',
            'parent'
        ],
        'hidden': {
            'child_id',
            'parent_id'
        },
        'readonly': {
            'child',
            'parent'
        }
    }
