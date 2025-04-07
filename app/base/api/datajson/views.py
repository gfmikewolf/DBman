from flask import jsonify
from app.database import db_session
from app.database.base import serialize_value
from app.extensions import DataJson, Base, db_session
from app.base.crud.utils import fetch_datajson_structure

def get_datajson_structure(datajson_id: str):
    datajson_cls = DataJson.class_map.get(datajson_id, None)
    if not datajson_cls:
        raise ValueError(f'Invalid datajson_id: {datajson_id}')
    with db_session() as db_sess:
        Base.db_session = db_sess
        structure = serialize_value(fetch_datajson_structure(datajson_cls, db_sess))
    
    return jsonify(success=True, data=structure)
