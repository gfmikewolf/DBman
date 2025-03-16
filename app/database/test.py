import sys
import os
from dotenv import load_dotenv
from sqlalchemy import Integer, select
from sqlalchemy.orm import ColumnProperty
from yaml import serialize 

sys.path.append('C:\\DBMan')

env_file = "env.development"

# 根据参数加载环境变量
load_dotenv(os.path.join(os.getcwd(), env_file))

from app.database import Base
from app.database.datajson import DataJson
from app.database.contract import Entity, Entitygroup
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
    
    if Base.db_session is None:
        raise Exception('db_session is None')
    with Base.db_session() as sess:
        r = sess.execute(select(Entity.entity_id, Entity.entity_name, Entity.entity_fullname, Entitygroup.entitygroup_name).join(Entity.entitygroup))
        for key, value in Entity.select_ref_names().items():
            print('\nref_name_key:', key)
            rn = sess.execute(value)
            print('\nref_names', tuple(rn.scalars()))
    
    if r is not None:
        for row in r:
            pass
            # print(row._mapping['entitygroup_name'])
    
    datatable_dict = Entity.fetch_datatable_dict()
    
    