# app/database/contract/clausetypes.py
from enum import Enum
from re import M

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