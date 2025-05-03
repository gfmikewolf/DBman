from sqlalchemy.types import TypeDecorator, JSON, String

class DataJsonType(TypeDecorator):
    """
    DataJson type decorator for SQLAlchemy.
    """
    impl = JSON
    cache_ok = True

    @property
    def python_type(self):
        from .base import DataJson
        return DataJson

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.data_dict(serializeable=True)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            # 局部导入 DataJson
            from .base import DataJson
            return DataJson.get_obj(value)
        return value

class TypeSetInt(TypeDecorator):
    impl = String

    @property
    def python_type(self) -> type:
        return set
    
    def process_bind_param(self, value: set[int] | None, dialect):
        if value is None:
            return None
        return ",".join(str(x) for x in value)

    def process_result_value(self, value: str | None, dialect):
        if value is None or value == "":
            return set()
        return {int(x.strip()) for x in value.split(",") if x.strip()}
