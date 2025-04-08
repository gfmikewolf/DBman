from enum import Enum

class ExpiryType(Enum):
    FIXED_EXPIRY_DATE = 'FD'
    LINKED_TO_CONTRACT = 'LC'
    LAST_CHILD_EXPIRY_DATE_OR_FIXED_DATE = 'LLOF'

