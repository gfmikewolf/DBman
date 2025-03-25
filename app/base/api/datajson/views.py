from typing import Any
from app.extensions import DataJson

def get_datajson_structure(datajson_id: str) -> dict[str, Any]:
    
    datajson_cls = DataJson.class_map.get(datajson_id, None)
    if not datajson_cls:
        raise ValueError(f'Invalid datajson_id: {datajson_id}')
    datajson_construct = datajson_cls.get_structure()
    return datajson_construct
