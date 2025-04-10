# contract/types.py
from enum import Enum

class ClauseAction(Enum):
    """
    { 'add', 'remove', 'update' }
    """
    ADD = 'add'
    REMOVE = 'remove'
    UPDATE = 'update'

class ClauseType(Enum):
    """
    { 'clause_entity', 'clause_scope', 'clause_expiry' }
    """
    BASIC = 'clause'
    ENTITY = 'clause_entity'
    SCOPE = 'clause_scope'
    EXPIRY = 'clause_expiry'

class ClausePos(Enum):
    """
    { 'mainbody', 'annex', 'appendix' }
    """
    MAINBODY = 'mainbody'
    ANNEX = 'annex'
    APPENDIX = 'appendix'  

class ExpiryType(Enum):
    FIXED_EXPIRY_DATE = 'FD'
    LINKED_TO_CONTRACT = 'LC'
    LAST_CHILD_EXPIRY_DATE_OR_FIXED_DATE = 'LLOF'
