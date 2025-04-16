# Removed unused import of 'false' from sqlalchemy

class Privilege:
    privs: dict[str, str] = {}
    
    def __init__(self):
        from app.extensions import Base, db_session
        with db_session() as sess:
            user_role = Base.model_map['user_role']
            anonymous_role = sess.query(user_role).filter_by(
                user_role_name='_anonymous' 
            ).first()
        if anonymous_role:
            self.privs = anonymous_role.table_privilege # type: ignore
    
    def match(self, privs: dict[str, str]) -> bool:
        for table, rw in privs.items():
            if table not in self.privs and '_all' not in self.privs:
                return False
            self_rw = self.privs.get(table, None) or self.privs.get('_all', {})
            if not rw:
                continue
            if rw not in self_rw:
                return False
        return True


