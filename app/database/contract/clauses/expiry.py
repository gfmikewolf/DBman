from enum import Enum, auto
from datetime import date
from app.database.datajson import DataJson

class ExpiryType(Enum):
    Date = auto()
    linked_to_Contract = auto()
    later_of_last_COA_or_Date = auto()

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
    
    expiry_type: ExpiryType = ExpiryType.Date
    expiry_date: date | None = date(1981, 12, 5)
    linked_contract_id: int | None = 0
    attr_info = {
        'data': {'expiry_type', 'expiry_date', 'linked_contract_id'},
        'required': {'expiry_type'},
        'ref_map': {
            'linked_contract_id': {
                'ref_table': 'contract', 
                'ref_pk': 'contract_id',
                'ref_name': 'contract_name',
                'order_by': ['contract_name'] 
            }
        }
    }
