# contract/types.py
from enum import Enum

class ClauseAction(Enum):
    """
    { 'add', 'remove', 'update' }
    """
    A = 'add'
    R = 'remove'
    U = 'update'

class ClauseType(Enum):
    """
    { 'clause_entity', 'clause_scope', 'clause_expiry' }
    """
    BASIC = 'clause without structured data'
    ENTITY = 'entity'
    SCOPE = 'scope'
    EXPIRY = 'expiry'

class ClausePos(Enum):
    """
    { 'mainbody', 'annex', 'appendix' }
    """
    M = 'mainbody'
    AN = 'annex'
    AP = 'appendix'  

class ExpiryType(Enum):
    FD = 'fixed expiry date'
    LC = 'linked to another contract'
    LL = 'later of last child contract or an expiry date'
