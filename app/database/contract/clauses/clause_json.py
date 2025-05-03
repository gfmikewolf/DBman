from app.database.base import DataJson
from ..dbmodels import Clause

class ClauseJson(DataJson):
    """
    ClauseJson class for Clause.clause_json Base class.
    """
    __datajson_id__ = 'clause_json'

    def bind_clause(self, clause: Clause) -> None:
        """
        Bind the Clause instance to the ClauseJson instance.

        :param clause: The Clause instance to bind.
        """
        self.clause = clause
