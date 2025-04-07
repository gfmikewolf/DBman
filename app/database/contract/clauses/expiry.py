from enum import Enum, auto
from datetime import date
from app.database.base import DataJson
from app.database.contract.dbmodels import Contract

class ExpiryType(Enum):
    FIXED_EXPIRY_DATE = 'FD'
    LINKED_TO_CONTRACT = 'LC'
    LAST_CHILD_EXPIRY_DATE_OR_FIXED_DATE = 'LLOF'

class ClauseExpiry(DataJson):
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

    constraints:
        - expiry_date is required if expiry_type is Date or later_of_last_COA_or_Date.
        - linked_contract_id is required if expiry_type is linked_to_Contract.
    """
    __datajson_id__ = 'clause_expiry'
    
    expiry_type: ExpiryType = ExpiryType.FIXED_EXPIRY_DATE
    expiry_date: date | None = date(1981, 12, 5)
    linked_contract_id: int | None = 0
    key_info = {
        'data': ('expiry_type', 'expiry_date', 'linked_contract_id'),
        'required': {'expiry_type'}
    }
    rel_info = {
        'linked_contract': {
            'ref_table': Contract,
            'local_col': 'linked_contract_id',
            'select_order': (Contract.contract_name,)
        }
    }
