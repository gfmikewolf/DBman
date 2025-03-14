import sys
import os
from dotenv import load_dotenv
from sqlalchemy import Integer, select
from sqlalchemy.orm import ColumnProperty 

sys.path.append('D:\\DBMan\\ver 1.0\\zeta')

env_file = "env.development"

# 根据参数加载环境变量
load_dotenv(os.path.join(os.getcwd(), env_file))

from app.database import Base
from app.database.datajson import DataJson
from app.database.contract import Entitygroup, Entity
from app.database.contract.clauses import ClauseEntity


if __name__ == '__main__':

    DataJson.class_map = {
        'clause_entity': ClauseEntity
    }
    clause2 = ClauseEntity('{"_cls_type": "clause_entity", "entity_id": 2.1, "action": "remove"}')

    clause1 = ClauseEntity({
        'action': 'adD',
        'entity_id': 1.6,
    })

    with Base.db_session() as sess: # type: ignore
        r = sess.get(Entity, 1)
        print(Entity.entity_id.column in Entity.__mapper__.columns)
