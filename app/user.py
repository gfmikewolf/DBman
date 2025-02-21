# app/user.py
from typing import List
from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.orm import Session
from datetime import date
from .base_mixin import Base, ForeignKeyMixin

class UserRole(Base):
    __tablename__ = 'user_role'
    user_role_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    user_role_name: Mapped[str]
    
    id = synonym('user_role_id');
    name = synonym('user_role_name')

    users: Mapped[List['User']] = relationship(
        back_populates='user_roles', 
        lazy='select',
        secondary='map_user__user_role')

class User(ForeignKeyMixin,Base):
    __tablename__ = 'user'
    user_id: Mapped[int] = mapped_column(primary_key=True, info={'readonly': True, 'hidden': True})
    user_name: Mapped[str]
    user_password_hash: Mapped[str] = mapped_column(info={'readonly': True})

    id = synonym('user_id')
    name = synonym('user_name')

    user_roles: Mapped[List['UserRole']] = relationship(
        back_populates='users', 
        lazy='select',
        secondary='map_user__user_role')
    
    @classmethod
    def get_options_fk(cls, session: Session):
        order_by_attr = {
            "user_role": "user_role_name",
        }
        return super().get_options_fk(session, order_by_attr=order_by_attr)

class MAPUserANDUserRole(ForeignKeyMixin, Base):
    __tablename__ = 'map_user__user_role'
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.user_id'),
        primary_key=True,
        info={
            'rel_name': 'user', 
            'fk_attr_name':'user_name'
        }
    )
    user_role_id: Mapped[int] = mapped_column(
        ForeignKey('user_role.user_role_id'),
        primary_key=True,
        info={
            'rel_name': 'user_role', 
            'fk_attr_name':'user_role_name'
        }
    )
