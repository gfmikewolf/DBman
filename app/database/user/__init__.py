# user/__init__.py

__all__ = [
    'User',
    'UserRole',
    'UserMAPUserRole'
]

from .dbmodels import (
    User, 
    UserRole, 
    UserMAPUserRole
)

user_model_map = {
    'user': User,
    'user_role': UserRole,
    'user__map__user_role': UserMAPUserRole
}

user_table_map = {
    'user': {
        'user',
        'user_role',
        'user__map__user_role'
    }
}
