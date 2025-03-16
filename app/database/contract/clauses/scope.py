from app.database.datajson import DataJson
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
    
    action: ClauseAction
    scope_id: int
    old_scope_id: int | None
    
    attr_info = {
        'data_keys': ['action', 'scope_id', 'old_scope_id'],
        'required_keys': ['action', 'scope_id'],
        'ref_map': {
            'scope_id': {
                'ref_table_name': 'scope', 
                'fk_attr_name': 'scope_id',
                'ref_attr_name': 'scope_name',
                'order_by_attr_names': ['scope_name'] 
            },
            'old_scope_id': {
                'ref_table_name': 'scope', 
                'fk_attr_name': 'scope_id',
                'ref_attr_name': 'scope_name',
                'order_by_attr_names': ['scope_name'] 
            }
        }
    }