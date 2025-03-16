# app/database/contract/clausetypes.py
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
    { 'entity', 'scope', 'expiry' }
    """
    ENTITY = 'entity'
    SCOPE = 'scope'
    EXPIRY = 'expiry'

class ClausePos(Enum):
    """
    { 'mainbody', 'annex', 'appendix' }
    """
    MAINBODY = 'mainbody'
    ANNEX = 'annex'
    APPENDIX = 'appendix'