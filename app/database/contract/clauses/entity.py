from sqlalchemy import select, Select
from app.database.base import DataJson
from ..clausetypes import ClauseAction
from ..dbmodels import Entity

class ClauseEntity(DataJson):
    """
    A clause entity data object.

    :ivar ClauseAction action: 
        One of {'add', 'update', 'delete'} to be performed on Entity.
    :ivar int entity_id: 
        The identifier mapping to the Entity table.
    :ivar int | None old_entity_id: 
        The old entity identifier, used only in update cases.

    :cvar str __datajson_id__: 
        The unique identifier for the DataJson type, set to 'clause_entity'.

    Constraints:
      - `action` is required.
      - `entity_id` is required.
      - `old_entity_id` is required if action is update.
    """
    __datajson_id__ = 'clause_entity'
    
    # Initiate cvars so that we can get the attribute types from class
    action: ClauseAction = ClauseAction.UPDATE
    entity_id: int = 0
    old_entity_id: int | None = 0
    
    attr_info = {
        'data': {'action', 'entity_id', 'old_entity_id'},
        'required': {'action', 'entity_id'},
        'foreign_keys': {
            'entity_id': 'Entity',
            'old_entity_id': 'Entity'
        },
        'ref_name_order': {
            'entity_name': ('entity_name',)
        }
    }