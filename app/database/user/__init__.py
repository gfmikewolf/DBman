# user/__init__.py

__all__ = [
    'User',
    'UserRole',
    'UserMAPUserRole'
]

from sqlalchemy import func
from .dbmodels import (
    User, 
    UserRole, 
    UserMAPUserRole,
    UserRoleMAPUserRole
)
cache_map = []

model_map = {
    'user': User,
    'user_role': UserRole,
    'user__map__user_role': UserMAPUserRole,
    'user_role__map__user_role': UserRoleMAPUserRole
}

table_map = {
    'user': [
        'user',
        'user_role',
        'user__map__user_role',
        'user_role__map__user_role'
    ]
}

func_map = {}