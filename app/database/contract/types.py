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
    CLAUSE = 'unstructured clause'
    CLAUSE_ENTITY = 'entity'
    CLAUSE_SCOPE = 'scope'
    CLAUSE_EXPIRY = 'expiry'
    CLAUSE_TERMINATION = 'termination'
    CLAUSE_CUSTOMER_LIST = 'customer list'
    CLAUSE_WARRANTY_PERIOD = 'warranty period'
    CLAUSE_COMMERCIAL_INCENTIVE = 'commercial incentive'
    CLAUSE_PAYMENT_TERM = 'payment term'
    CLAUSE_SUSPENSION = 'suspension'
    CLAUSE_LOL = 'limitation of liability'
    CLAUSE_SLA = 'service level of agreement'
    CLAUSE_STEPIN = 'step-in rights'
    CLAUSE_BCM = 'business continuity management'
    CLAUSE_LIQUIDATED_DAMAGES = 'liquidated damages'
    CLAUSE_INDEMNIFICATION = 'indemnification'
    CLAUSE_PRODUCT_LIFE_CYCLE = 'product life cycle'

class Milestone(Enum):
    POD = 'Proof Of Delivery'
    PAC = 'Provisional Acceptance Certificate'
    FAC = 'Final Acceptance Certificate'

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
