# clauses/entity.py
from app.database.base import DataJson
from app.database.contract.dbmodels import Entity

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
      - `old_entity_id` is required if action is ClauseAction.UPDATE.
    """
    __datajson_id__ = 'clause_entity'
    
    # Initiate cvars so that we can get the attribute types from class
    entity_id: int = 0
    old_entity_id: int | None = 0
    
    key_info = {
        'data': ('entity_id', 'old_entity_id', 'entity', 'old_entity'),
        'required': {'entity_id'},
        'hidden': {'entity_id', 'old_entity_id'}
    }
    rel_info = {
        'entity': {
            'ref_table': Entity,
            'local_col': 'entity_id',
            'order_by': (Entity.entity_name,)
        },
        'old_entity': {
            'ref_table': Entity,
            'local_col': 'old_entity_id',
            'select_order': ('entity_name',)
        }
    }
