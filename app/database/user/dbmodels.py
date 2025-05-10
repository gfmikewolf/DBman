import bcrypt
from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Session
from sqlalchemy.types import Integer
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
        lazy='selectin'
    )

    @property
    def role_family(self) -> set['UserRole']:
        sess = Session.object_session(self)
        if sess is None:
            raise Exception("DB Session is required for User instantiation")
        stmt = (
            select(UserRole)
            .join(UserMAPUserRole)
            .where(UserMAPUserRole.user_id == self.user_id)
        )
        direct_roles = set(sess.scalars(stmt))
        initial_role_ids = {ur.user_role_id for ur in direct_roles}
        direct_role_parents = (
            select(UserRoleMAPUserRole.parent_id)
            .where(UserRoleMAPUserRole.child_id.in_(initial_role_ids))
            .cte(recursive=True)
        )
        ancestors = direct_role_parents.union(
            select(UserRoleMAPUserRole.parent_id)
            .join(
                direct_role_parents,
                UserRoleMAPUserRole.child_id == direct_role_parents.c.parent_id
            )
        )

        stmt = (
            select(UserRole)
            .join(
                ancestors,
                UserRole.user_role_id == ancestors.c.parent_id
            )
        )
        return set(sess.scalars(stmt)) | direct_roles

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

    data_list = [
        'user_name',
        'user_password',
        'user_roles'
    ]
    key_info = {
        'hidden': {'user_password'},
        'readonly': {'user_roles'},
        'viewable_list': {'user_roles'},
        'password': { 'user_password' }
    }
class UserRole(Base):
    __tablename__ = 'user_role'
    user_role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_role_name: Mapped[str]
    
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
        lazy='selectin'
    )
    children: Mapped[list['UserRole']] = relationship(
        back_populates='parents',
        secondary=lambda: UserRoleMAPUserRole.__table__,
        primaryjoin=lambda: UserRole.user_role_id == UserRoleMAPUserRole.parent_id,
        secondaryjoin=lambda: UserRole.user_role_id == UserRoleMAPUserRole.child_id,
        lazy='selectin'
    )
    @property
    def role_family(self) -> set['UserRole']:
        direct_parents_cte = (
            select(UserRoleMAPUserRole.parent_id.label('id'))
            .where(UserRoleMAPUserRole.child_id == self.user_role_id)
            .cte(recursive=True)
        )

        family_ids = direct_parents_cte.union(
            select(UserRoleMAPUserRole.parent_id)
            .join(direct_parents_cte, UserRoleMAPUserRole.child_id == direct_parents_cte.c.id)
        )

        sess = Session.object_session(self)
        if sess is None:
            raise Exception("DB Session is required for User instantiation")
        stmt = select(UserRole).join(family_ids, UserRole.user_role_id == family_ids.c.id)
        return set(sess.scalars(stmt)) | {self}
    def __str__(self) -> str:
        return self.user_role_name
    
    data_list = [
        'user_role_name',
        'table_privilege',
        'parents',
        'children'
    ]
    key_info = {
        'viewable_list': {'users', 'parents', 'children'},
        'readonly': {'users', 'parents', 'children'}
    }
class UserMAPUserRole(Base):
    __tablename__ = 'user__map__user_role'
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'), primary_key=True)
    user_role_id: Mapped[int] = mapped_column(Integer, ForeignKey('user_role.user_role_id'), primary_key=True)
    user: Mapped['User'] = relationship(lazy='selectin', overlaps='users, user_roles')
    user_role: Mapped['UserRole'] = relationship(lazy='selectin', overlaps='users, user_roles')
    
    def __str__(self) -> str:
        return f'{self.user} ∈ {self.user_role}'
    
    data_list = [
        'user_id',
        'user_role_id',
        'user',
        'user_role'
    ]
    key_info = {
        'hidden': {'user_id', 'user_role_id'},
        'readonly': {'user', 'user_role'}
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
    
    data_list = [
        'child_id',
        'parent_id',
        'child',
        'parent'
    ]
    key_info = {
        'hidden': {'child_id', 'parent_id'},
        'readonly': {'child', 'parent'}
    }
