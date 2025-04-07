from app.database.base import DataJson
from app.database.contract.dbmodels import Scope

class ClauseScope(DataJson):
    """
    attributes:
        action (ClauseAction): 
            - Add, Remove, Novate
        scope_id (int): 
            - map table scope
        old_scope_id (int | None): 
            - only used in Novation

    constraints:
        - action is required.
        - scope_id is required.
        - old_scope_id is required if action is Novate.
    """
    __datajson_id__ = 'clause_scope'
    
    scope_id: int = 0
    old_scope_id: int | None = 0
    
    key_info = {
        'data': ('scope_id', 'old_scope_id'),
        'required': {'scope_id'}
    }
    rel_info = {
        'scope': {
            'ref_table': Scope,
            'local_col': 'scope_id',
            'select_order': (Scope.scope_name,)
        },
        'old_scope': {
            'ref_table': Scope,
            'local_col': 'old_scope_id',
            'select_order': (Scope.scope_name,)
        }
    }