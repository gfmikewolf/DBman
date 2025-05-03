from datetime import date
from typing import Iterable
from .clause_json import ClauseJson
from ..dbmodels import Contract, Scope
from .types import ExpiryType

class ClauseExpiry(ClauseJson):
    """
    attributes:
        - expiry_type (ExpiryType): 
            - Date for fixed expiry date
            - linked_to_Contract for expire with the linked contract
            - later_of_last_COA_or_Date for expire with the later of last COA or a date
        - expiry_date (date | None): 
            - Required if expiry_type is Date or later_of_last_COA_or_Date
        - linked_contract_id (int | None): 
            - Required if expiry_type is linked_to_Contract
        - scope_id (int | None):
            - Optional.
            - if None, expiry applies to the whole amendment

    constraints:
        - expiry_date is required if expiry_type is Date or later_of_last_COA_or_Date.
        - linked_contract_id is required if expiry_type is linked_to_Contract.
    """
    __datajson_id__ = 'clause_expiry'
    scope_id: int | None = 0
    expiry_type: ExpiryType = ExpiryType.FIXED_EXPIRY_DATE
    expiry_date: date | None = date(1981, 12, 5)
    linked_contract_id: int | None = 0
    key_info = {
        'data': (
            'expiry_type', 
            'expiry_date',
            'linked_contract',
            'linked_contract_id',
            'applied_to_scope', 
            'scope_id'
        ),
        'required': {
            'expiry_type'
        }
    }
    rel_info = {
        'linked_contract': {
            'ref_table': Contract,
            'local_col': 'linked_contract_id',
            'select_order': (Contract.contract_name,)
        },
        'applied_to_scope': {
            'ref_table': Scope,
            'local_col': 'scope_id',
            'select_order': (Scope.scope_name,)
        }
    }

    def validate(
        self, 
        valid_contract_ids: Iterable[int] | None = None
    ) -> bool:
        """
        Validate the constraints for the ClauseExpiry.

        :return: True if all constraints are valid, False otherwise.
        :param clause: The Clause instance to validate against.
        """
        flag = False
        if self.expiry_type == ExpiryType.FIXED_EXPIRY_DATE or ExpiryType.LAST_CHILD_EXPIRY_DATE_OR_FIXED_DATE:
            flag = self.expiry_date is not None and self.linked_contract_id is None
        elif self.expiry_type == ExpiryType.LINKED_TO_CONTRACT:
            flag = self.linked_contract_id is not None and self.expiry_date is None
            if valid_contract_ids:
                flag = flag and self.linked_contract_id in valid_contract_ids #type: ignore

        return flag
