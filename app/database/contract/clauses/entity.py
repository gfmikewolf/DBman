from app.database.datajson import DataJson
from app.database.contract.types import ClauseAction
from sqlalchemy import select, Select
from app.database.contract.dbmodels import Entity

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
        'required': {'action', 'entity_id'}
    }

    def __init__(self, data: str | dict | None, **kwargs):
        super().__init__(data, **kwargs)

    @classmethod
    def select_all(cls, with_ref_name=True) -> Select:
        if with_ref_name:
            return select(
                Entity.entity_id, 
                Entity.entity_name, 
                Entity.entity_fullname
            ).select_from(Entity)
        return select(
            Entity.entity_id, 
            Entity.entity_name, 
            Entity.entity_fullname
        ).select_from(Entity)