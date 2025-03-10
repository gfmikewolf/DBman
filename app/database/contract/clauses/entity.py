from app.database.jsonbase import JsonBase
from app.database.contract.types import ClauseType, ClauseAction

class ClauseEntity(JsonBase):
    """
    attributes:
        action (ClauseAction): 
            - Add, Remove, Novate
        entity_id (int): 
            - map table entity
        old_entity_id (int | None): 
            - only used in Novation

    constraints:
        - action is required.
        - entity_id is required.
        - old_entity_id is required if action is Novate.
    """
    type: ClauseType = ClauseType.ENTITY
    action: ClauseAction
    entity_id: int
    old_entity_id: int | None
    
    attr_info_keys = {
        'data': {'action', 'entity_id', 'old_entity_id'},
        'required': {'action', 'entity_id'},
        'ref_map': {
            'entity_id': {
                'ref_table_name': 'entity', 
                'fk_attr_name': 'entity_id',
                'ref_attr_name': 'entity_name',
                'order_by': {'entity_name': 'ASC'}
            },
            'old_entity_id': {
                'ref_table_name': 'entity', 
                'fk_attr_name': 'entity_id',
                'ref_attr_name': 'entity_name',
                'order_by_attr_names': {'entity_name': 'ASC'} 
            }
        }
    }