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
    CLAUSE_PRODUCT_LIFECYCLE = 'product lifecycle'
    CLAUSE_CURRENCY = 'currency'
    CLAUSE_NOTICE = 'notice'
    CLAUSE_TPM = 'third party management'
    CLAUSE_COMPLIANCE = 'compliance'
    CLAUSE_APPLICABLE_LAW = 'applicable law'

class Milestone(Enum):
    POD = 'Proof Of Delivery'
    PAC = 'Provisional Acceptance Certificate'
    FAC = 'Final Acceptance Certificate'
    GPB = 'GPB introduction date'
    EOL = 'EOL'
    GA = 'General Availability'

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

class PeriodUnit(Enum):
    CDAY = 'calendar days'
    WDAY = 'work days'
    MON = 'months'
    YEAR = 'years'

class InterestBase(Enum):
    LIBOR = 'LIBOR'
    EIBOR = 'EIBOR'
    LENDING = 'prevailing lending rate'

class LifecyclePhase(Enum):
    MARKET = '➔EOM'
    SUPPORT = '➔EOS'
    END_OF_LIFE = '➔EOL'

class TPMType(Enum):
    CBC = 'case by case'
