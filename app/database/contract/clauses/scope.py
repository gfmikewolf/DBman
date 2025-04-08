from typing import Iterable
from ..types import ClauseAction
from ..dbmodels import Clause, Scope
from .clause_json import ClauseJson

class ClauseScope(ClauseJson):
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
    
    key_info = {
        'data': ('scope_id', 'old_scope_id'),
        'required': {'scope_id'}
    }
    rel_info = {
        'scope': {
            'ref_table': Scope,
            'local_col': 'scope_id',
            'select_order': (Scope.scope_name,)
        },
        'old_scope': {
            'ref_table': Scope,
            'local_col': 'old_scope_id',
            'select_order': (Scope.scope_name,)
        }
    }
    def validate(
        self, clause: Clause, 
        valid_scope_ids: Iterable[int] | None = None,
        current_entities: Iterable[int] | None = None
    ) -> bool:
        """
        Validate the constraints for the ClauseScope.

        :return: True if all constraints are valid, False otherwise.
        :param clause: The Clause instance to validate against.
        :param valid_scope_ids: A list of valid scope IDs to check against.
        :param current_entities: A list of current scope IDs to check against.
        """
        flag = False
        if valid_scope_ids:
            flag = flag and self.scope_id in valid_scope_ids

        if clause.clause_action == ClauseAction.ADD:
            flag = not self.old_scope_id
            if current_entities is not None:
                flag = flag and (self.scope_id not in current_entities)
        elif clause.clause_action == ClauseAction.REMOVE:
            flag = not self.old_scope_id
            if current_entities is not None:
                flag = flag and (self.scope_id in current_entities)
        elif clause.clause_action == ClauseAction.UPDATE:
            flag = self.old_scope_id is not None and self.old_scope_id != self.scope_id
            if valid_scope_ids:
                flag = flag and (self.old_scope_id in valid_scope_ids) # type: ignore
            if current_entities is not None:
                flag = flag and (self.old_scope_id in current_entities) # type: ignore
                flag = flag and (self.scope_id not in current_entities)
        return flag
