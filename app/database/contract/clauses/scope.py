from app.database.base import DataJson
from ..clausetypes import ClauseAction

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
    
    attr_info = {
        'data': {'scope_id', 'old_scope_id'},
        'required': {'scope_id'},
        'rel_map': {
            'scope': {
                'ref_table': 'scope',
                'local_col': 'scope_id',
                'name_col': 'scope_name',
                'select_order': ('scope_name',)
            },
            'old_scope': {
                'ref_table': 'scope',
                'local_col': 'old_scope_id',
                'name_col': 'scope_name',
                'select_order': ('scope_name',)
            }
        }
    }