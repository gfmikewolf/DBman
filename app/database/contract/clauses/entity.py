# clauses/entity.py
from typing import Iterable
from ..types import ClauseAction
from ..dbmodels import Entity
from .clause_json import ClauseJson

class ClauseEntity(ClauseJson):
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
    clause_action: ClauseAction = ClauseAction.ADD
    entity_id: int = 0
    old_entity_id: int | None = 0
    
    key_info = {
        'data': (
            'clause_action',
            'entity_id', 
            'old_entity_id', 
            'entity', 
            'old_entity'),
        'required': {'entity_id', 'clause_action'},
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
    
    def validate(
        self,
        valid_entity_ids: Iterable[int] | None = None,
        current_entities: Iterable[int] | None = None
    ) -> bool:
        """
        Validate the constraints for the ClauseEntity.

        :return: True if all constraints are valid, False otherwise.
        :param clause: The Clause instance to validate against.
        :param valid_entity_ids: A list of valid entity IDs to check against.
        :param current_entities: A list of current entity IDs to check against.
        """
        flag = False
        if valid_entity_ids:
            flag = flag and self.entity_id in valid_entity_ids

        if self.clause_action == ClauseAction.ADD:
            flag = not self.old_entity_id
            if current_entities is not None:
                flag = flag and (self.entity_id not in current_entities)
        elif self.clause_action == ClauseAction.REMOVE:
            flag = not self.old_entity_id
            if current_entities is not None:
                flag = flag and (self.entity_id in current_entities)
        elif self.clause_action == ClauseAction.UPDATE:
            flag = self.old_entity_id is not None and self.old_entity_id != self.entity_id
            if valid_entity_ids:
                flag = flag and (self.old_entity_id in valid_entity_ids) # type: ignore
            if current_entities is not None:
                flag = flag and (self.old_entity_id in current_entities) # type: ignore
                flag = flag and (self.entity_id not in current_entities)
        return flag
