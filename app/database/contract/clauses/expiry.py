from enum import Enum, auto
from datetime import date
from app.database.jsonbase import JsonBase

class ExpiryType(Enum):
    Date = auto()
    linked_to_Contract = auto()
    later_of_last_COA_or_Date = auto()

class ClauseExpiry(JsonBase):
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
    expiry_type: ExpiryType
    expiry_date: date | None
    linked_contract_id: int | None
    attr_info = {
        'data_keys': ['expiry_type', 'expiry_date', 'linked_contract_id'],
        'required_keys': ['expiry_type'],
        'readonly_keys': [],
        'ref_map': {
            'linked_contract_id': {
                'ref_table_name': 'contract', 
                'fk_attr_name': 'contract_id',
                'ref_attr_name': 'contract_name',
                'order_by_attr_names': ['contract_name'] 
            }
        }
    }
