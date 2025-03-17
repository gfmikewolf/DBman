import sys
import os
from dotenv import load_dotenv
from sqlalchemy import select

sys.path.append('C:\\DBMan')

env_file = "env.development"

# 根据参数加载环境变量
load_dotenv(os.path.join(os.getcwd(), env_file))

from app.database import db_session
from app.database.base import Base
from app.database.datajson import DataJson
from app.database.contract import Entity, Entitygroup, Amendment, Contract, Clause
from app.database.contract.clauses import ClauseEntity


if __name__ == '__main__':

    DataJson.class_map = {
        'clause_entity': ClauseEntity
    }

    Base.model_map = {
        'entity': Entity,
        'entitygroup': Entitygroup
    }

    testClause = {
        'extra_data': 0.5,
        '__datajson_id__': 'clause_entity',
        'action': 'aDd',
        'entity_id': '100',
        'old_entity_id': 200
    }
    
    testEntity = {
        'extra_data': 0.6,
        'entity_id': 1000,
        'entity_name': 'test',
        'entity_fullname': 'test entity',
        'entitygroup_id': 2000
    }

    print('\n--- ClauseEntity test ---')
    clause = DataJson.get_obj(testClause)
    if clause is not None:
        print(clause.get_keys('data'))

    print('\n\n--- Entity test ---')
    
    with db_session() as sess:
        Base.db_session = sess
        print(Entity.fetch_datatable_dict())
    