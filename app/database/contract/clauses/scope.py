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
    __datajson_id__ = 'clause_expiry'
    
    action: ClauseAction = ClauseAction.UPDATE
    scope_id: int = 0
    old_scope_id: int | None = 0
    
    attr_info = {
        'data': ['action', 'scope_id', 'old_scope_id'],
        'required': ['action', 'scope_id'],
        'ref_map': {
            'scope_id': {
                'ref_table': 'scope', 
                'ref_pk': 'scope_id',
                'ref_name': 'scope_name',
                'order_by': ['scope_name'] 
            },
            'old_scope_id': {
                'ref_table': 'scope', 
                'ref_pk': 'scope_id',
                'ref_name': 'scope_name',
                'order_by': ['scope_name'] 
            }
        }
    }