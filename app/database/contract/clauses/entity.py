from app.database.base import DataJson

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
    old_entity_id: int | None = 0
    
    attr_info = {
        'data': {'old_entity_id'},
        'rel_map': {
            'old_entity': {
                'ref_table': 'entity',
                'local_col': 'old_entity_id',
                'name_col': 'entity_name',
                'select_order': ('entity_name',)
            }
        }
    }
