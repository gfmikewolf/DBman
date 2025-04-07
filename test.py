from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.base.crud.utils import fetch_tabledata
from app.extensions import db_session, Base, DataJson

if __name__ == "__main__":
    with db_session() as db_sess:
        print(fetch_tabledata(Base.model_map['clause'], db_sess))