from flask import jsonify
from app.database.base import serialize_value
from app.extensions import DataJson

def get_datajson_structure(datajson_id: str):
    datajson_cls = DataJson.class_map.get(datajson_id, None)
    if not datajson_cls:
        raise ValueError(f'Invalid datajson_id: {datajson_id}')
    structure = serialize_value(datajson_cls.get_structure())
    return jsonify(success=True, data=structure)
