from sqlalchemy import create_engine, ForeignKey, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, relationship, synonym
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column

# app/base_mixin.py
from typing import List, Type
from sqlalchemy import select, Select
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.sql.expression import ColumnClause


class Base(DeclarativeBase):
    
    # 当前用户可访问的表与数据模型的映射
    map_table_Model = {}

    # 查询所有数据，排除特定信息的列属性，添加关联模型的属性
    @classmethod
    def query_all(cls, exclude: List[str]=['hidden'], with_ref_attrs: bool=True) -> Select:
        query_columns = []
        for ex_info in exclude:
            exclude_columns = cls.attr_info.get(ex_info, [])
            for attr in cls.__mapper__.column_attrs:
                if attr not in exclude_columns:
                    query_columns.append(attr)
        join_models = []
        if with_ref_attrs:
            ref_map = cls.attr_info.get('ref_map', {})
            for join_model, attr_orderby_dict in ref_map.items():
                for ref_name_attr in attr_orderby_dict.keys():
                    if ref_name_attr is not None and join_model is not None:
                        query_columns.append(ref_name_attr)
                        join_models.append(join_model)
        query = select(*query_columns)
        if join_models:
            query = query.select_from(cls)
            for model in join_models:
                query = query.join(model)
        return query
    
    # 获取关联属性的选项
    @classmethod
    def query_all_ref_attrs(cls, new_order_by: dict[ColumnProperty, List[ColumnProperty | ColumnClause]]={}) -> dict[ColumnProperty, Select]:
        queries = {}
        ref_map = cls.attr_info.get('ref_map', {})
        for model, attr_orderby_dict in ref_map.items():
            query_columns = []
            order_by_columns = []
            for ref_name_attr, order_by in attr_orderby_dict.items():
                if ref_name_attr is not None and model is not None:
                    query_columns.append(ref_name_attr)
                    replace_order_by = []
                    if new_order_by:
                        replace_order_by = new_order_by.get(ref_name_attr, [])
                    if replace_order_by:
                        order_by_columns.extend(replace_order_by)
                    elif order_by:
                        order_by_columns.extend(order_by)
                    query = select(*query_columns)
                    if order_by_columns:
                        query = query.order_by(*order_by_columns)
                    queries[ref_name_attr] = query
        return queries

class Type(Base):
    __tablename__ = 'types'
    id: Mapped[int] = mapped_column(primary_key=True)
    type_name: Mapped[str] = mapped_column()
    type_info: Mapped[str | None] = mapped_column()
    
    name = synonym('type_name')
    users: Mapped['User'] = relationship('User', back_populates='type')

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    type_id: Mapped[int] = mapped_column(ForeignKey('types.id'))
    type: Mapped['Type'] = relationship(back_populates='users', lazy='selectin')
    
    attr_info = {
        'hidden': [id, type_id],
        'readonly': [id],
        'ref_map': {
            Type: {Type.name:[]}
        }
    }

    @hybrid_property
    def type_name(self):
        return self.type.name
    
    @type_name.expression
    def type_name(cls):
        return Type.name

Map = {
    'users': User,
    'types': Type
}

if __name__ == "__main__":
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    with session as sess:
        user1 = User(name='John')
        user1.type = Type(name='Admin')
        user2 = User(name='Jane')
        user2.type = Type(name='User')
        session.add(user1)
        session.add(user2)
        session.commit()
        for attr, query in User.query_all_ref_attrs().items():
            result = sess.execute(query)
            print(f'{attr}: {[row for row in result]}')
        print(f'\nall types: {sess.execute(select(Type.name)).all()}')