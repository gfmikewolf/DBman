from app.database.datajson import DataJson
from app.database.contract.types import ClauseAction

class ClauseEntity(DataJson):
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
    _cls_type = 'clause_entity'
    
    action: ClauseAction = ClauseAction.UPDATE
    entity_id: int = 0
    old_entity_id: int | None = None
    
    attr_info = {
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

    def __init__(self, data: str | dict | None, **kwargs):
        super().__init__(data, **kwargs)