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
    CLAUSE = 'clause without structured data'
    CLAUSE_ENTITY = 'entity'
    CLAUSE_SCOPE = 'scope'
    CLAUSE_EXPIRY = 'expiry'

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
