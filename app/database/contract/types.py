from enum import Enum

class ClauseAction(Enum):
    ADD = 'add'
    REMOVE = 'remove'
    UPDATE = 'update'

class ClauseType(Enum):
    ENTITY = 'entity'
    SCOPE = 'scope'
    EXPIRY = 'expiry'

class ClausePos(Enum):
    MAINBODY = 'mainbody'
    ANNEX = 'annex'
    APPENDIX = 'appendix'