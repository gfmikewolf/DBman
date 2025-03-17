# app/database/base.py

__all__ = ['Base']

# python
from copy import deepcopy
from sqlite3 import DatabaseError
from typing import Any, Iterable
from enum import Enum # 用到eval('Enum')，需要导入
from datetime import date # 用到eval('date')，需要导入
# sqlalchemy
from sqlalchemy import Column, select, Select
from sqlalchemy.orm import DeclarativeBase, Session
# app
from app.utils.common import args_to_dict
from .datajson import convert_value_by_python_type, serialize_value
from .datajson import DataJson # 用到eval('DataJson')，需要导入

class Base(DeclarativeBase):
    """
    数据模型基类。

    映射规则：
    - 数据模型的属性名必须与数据库列名一致。
    - 对可以简单引用记录名称的表使用 name = synonym(引用属性名称)
    - 对于单主键场景，主键属性不为id时，使用id = synonym(主键属性名称)

    属性：
    - db_session (scoped_session | None): SQLAlchemy 会话对象，用于与数据库进行交互。
    - model_map (dict[str, type[Base]]): 当前用户可访问的表与数据模型的映射。
    - col_key_info (dict[str, set[str]]): 数据库列的信息字典{信息字段：数据库列名的集合}。用于缓存已获取的信息。
    - col_info (dict[str, set[Column]]): 数据库列的信息字典{信息字段：数据库列属性的集合}。用于缓存已获取的信息。

    公共方法：
    - 实例方法：
        - replace_data(data: str | dict | None = None, **kwargs: Any) -> None: 更新一个实例的数据。
        - data_dict(serializeable: bool = False) -> dict[str, Any]: 获取实例的数据字典，可选择转换类型为JSON可用的字典，字典会带有__tablename__标签，方便解析为实例。
    - 类方法：
        - validate_dict(data: dict[str, Any]) -> bool: 验证数据字典中的数据是否符合模型的属性要求。
        - load(data: dict | str | None = None, **kwargs) -> dict[str, Any]: 将JSON字符串或字典转换为字典。
        - fetch_datatable_dict() -> dict[str, Any]: 获取可用于渲染的数据表。
        - get_col_keys(*args: str) -> set[str]: 获取包含指定信息的列属性集合。
        - get_cols(*args: str) -> set[Column]: 获取包含指定信息的列属性集合。

    私有方法：
    - 类方法：
        - _load_dict(data: dict) -> dict[str, Any]: 将已验证的字典中对应col_info里'data'类型的数据按_tablename的类属性进行数据类型转换。
    """
    model_map: dict[str, type['Base']] = {}
    """
    当前用户可访问的表与数据模型的映射。

    - 该字典应该在 database/models.py 中初始化。
    """
    
    db_session: Session | None = None
    """
    SQLAlchemy 会话对象，用于与数据库进行交互。

    - 该对象应该在 database/__init__.py 中初始化。
    """

    col_key_info: dict[str, set[str] | dict[str, list[str]]] = NotImplemented
    """
    数据库列的信息字典{信息字段：数据库列名的集合}

    - 特别注意数据库列名与类模型属性名必须一致
    - 注意集合是无序的
    """
    col_info: dict[str, set[Column]] = NotImplemented
    """
    数据库列的信息字典{信息字段：数据库列属性的集合}

    - 注意集合是无序的
    """
    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        每个子类需要定义自己的类属性`col_info`和`col_key_info`，
        如果未定义，则在子类构建时初始化为空字典。
        """
        super().__init_subclass__(**kwargs)
        if cls.col_key_info is NotImplemented:
            cls.col_key_info = dict()
        if cls.col_info is NotImplemented:
            cls.col_info = dict()

    def replace_data(self, data: str | dict | None = None, **kwargs: Any) -> None:
        """
        更新一个实例的数据。如果数据字典中的数据不符合模型的属性要求，则抛出异常。
        如果字典里有多余的数据，但其他数据符合数据格式的要求，会继续执行。

        参数:
        data (str | dict | None): JSON 字符串或字典。
        kwargs (Any): 其他关键字参数。关键字参数优先级高于 data。
        """
        args_dict = args_to_dict(data, **kwargs)
        if self.get_cls_from_dict(args_dict) is None:
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {self}')
        mod_col_keys = self.get_col_keys('modifiable')
        if args_dict.keys() - mod_col_keys: # 检查是否有非法数据
            raise AttributeError(f'Invalid data: {args_dict} to match {self}')
        for key in mod_col_keys:
            if key in args_dict:
                setattr(self, key, args_dict[key])
       
    @classmethod
    def get_cols(cls, *args: str) -> set[Column]:
        """
        获取包含指定信息的列属性集合。
        
        参数:
        *args (str): 包含的信息字符串参数。
        
        返回:
        set[]: 包含指定信息的列属性集合。
        """
        cols = set()
        for info in args:
            # 如果已经缓存了信息，返回缓存信息
            if info in cls.col_info:
                cols.update(cls.col_info[info])
            # 如果没有缓存信息，根据参数获取信息并缓存
            elif info in {'readonly', 'hidden'}:
                info_keys = cls.col_key_info.get(info, set())
                if info_keys:
                    info_cols = {cls.__mapper__.columns[key] for key in info_keys}
                    cls.col_info[info] = info_cols
                    cols.update(info_cols)
            elif info == 'required':
                info_cols = set()
                for col in cls.__mapper__.columns:
                    # 如果该列不允许为空且不是自动增长字段，则认为是必填项
                    if (not col.nullable) and (col.autoincrement is not True):
                        info_cols.add(col)
                cls.col_key_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'data':
                info_cols = set(cls.__mapper__.columns)
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'pk':
                info_cols = set(cls.__mapper__.primary_key)
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'modifiable':
                info_cols = cls.get_cols('data') - cls.get_cols('readonly')
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'visible':
                info_cols = cls.get_cols('data') - cls.get_cols('hidden')
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info in {'date', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_cols = set()
                for col in cls.get_cols('data'):
                    if issubclass(col.type.python_type, eval(info)):
                        info_cols.add(col)
                cls.col_info[info] = info_cols
                cols.update(info_cols)
            elif info == 'fk':
                info_cols = set()
                for col in cls.get_cols('data'):
                    if col.foreign_keys:
                        info_cols.add(col)
                cls.col_info[info] = info_cols 
                cols.update(info_cols)   
            else:
                raise AttributeError(f'Invalid col info {info} for {cls}')
        return cols
    
    @classmethod
    def get_col_keys(cls, *args: str) -> set[str]:
        """
        获取包含指定信息的列属性集合。

        参数:
        *args (str): 包含的信息字符串参数。

        返回:
        set[]: 包含指定信息的列属性集合。
        """
        col_keys = set()
        for info in args:
            info_keys = cls.col_key_info.get(info, set())
            if not info_keys:
                info_keys = {col.name for col in cls.get_cols(info)}
                cls.col_key_info[info] = info_keys  
            col_keys.update(info_keys)
        return col_keys
    
    @classmethod
    def get_cls_from_dict(cls, data : dict[str, Any]) -> type['Base'] | None:
        """
        从数据字典中获取对应的类。调用Base类此方法，数据中必须包含__tablename__键。

        参数:
        data (dict[str, Any]): 数据字典。

        返回:
        type[Base] | None: 数据字典对应的类。
        """
        if cls.__tablename__ is None:
            tablename = data.get('__tablename__', None)
            model_cls = cls.model_map.get(tablename, None)
            if model_cls is None:
                raise AttributeError(f'Invalid {tablename} in class_map {cls.model_map}')
        else:
            tablename = cls.__tablename__
            model_cls = cls
        
        required_keys = model_cls.get_col_keys('required')
        # 找到required_keys中不存在于data.keys()的键
        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise AttributeError(f'Missing required keys: {missing_keys} in {data}')
        
        # 如果data_keys中有readonly的键，抛出属性异常
        readonly_keys = model_cls.get_col_keys('readonly')
        # 如果data_keys中有readonly_keys,下面的计算会得到非空集合
        if (readonly_keys - (readonly_keys - data.keys())):
            raise AttributeError(f'Readonly keys: {readonly_keys} in {data}')
        return model_cls
    
    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
        """
        将JSON字符串或字典转换为字典。

        参数:
        data (dict | str | None): JSON字符串或字典。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        args_dict = args_to_dict(data, **kwargs)
        model_cls = cls.get_cls_from_dict(args_dict)
        if model_cls is None:
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {cls}')

        if not args_dict:
            return args_dict
        else:
            return model_cls._load_dict(args_dict)
          
    @classmethod
    def _load_dict(cls, data: dict) -> dict[str, Any]:   
        """
        将已验证的字典中对应col_info里'data'类型的数据按_tablename的类属性进行数据类型转换。
        - 忽略'readonly'键的数据

        参数:
        data (dict): 经验证的数据。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        if cls.__tablename__ is None:
            model_cls = cls.get_cls_from_dict(data)
            if model_cls is None:
                raise AttributeError(f'Invalid data {data} for {cls}')
            tablename = model_cls.__tablename__
        else:
            tablename = cls.__tablename__
            model_cls = cls
                  
        mod_cols = model_cls.get_cols('modifiable')

        data_dict = {}
        data_dict['__tablename__'] = tablename
        
        for mod_col in mod_cols:
            value = data.get(mod_col.name, None)
            if value is not None:
                data_dict[mod_col.name] = convert_value_by_python_type(value, mod_col)
        return data_dict

    def __setattr__(self, key: str, value: Any) -> None:
        """
        设置属性值。如果属性是只读属性，则不进行设置。如果是数据属性，则根据属性类型转换值。
        """
        converted_value = value
        if key in self.get_col_keys('data'):
            readonly_keys = self.get_col_keys('readonly')
            if key in readonly_keys:
                raise AttributeError(f'Key {key} is readonly for {self}')
            attr = getattr(self.__class__, key, None)
            if attr is None:
                raise AttributeError(f'Invalid key {key} for {self}')
            if hasattr(attr, 'type') and hasattr(attr.type, 'python_type'):
                converted_value = convert_value_by_python_type(value, attr.type.python_type)
        super().__setattr__(key, converted_value)
   
    def data_dict(self, serializeable: bool = False) -> dict[str, Any]:
        data_dict = {'__tablename__': self.__tablename__}
        data_keys = self.get_col_keys('data')
        for data_key in data_keys:
            attr = getattr(self, data_key, None)
            if attr is None:
                raise AttributeError(f'Invalid attribute {data_key} for {self}')
            data_dict[data_key] = serialize_value(attr) if serializeable else attr
        return data_dict

    @classmethod
    def _validate_session(cls) -> bool:
        if cls.db_session is None:
            return False
        try:
            cls.db_session.scalar(select(1))
        except DatabaseError as e:
            return False
        return True
    
    @classmethod
    def fetch_datatable_dict(cls) -> dict[str, Any]:
        if cls._validate_session() is False:
            raise DatabaseError('Invalid db_session {cls.db_session} for {cls}')
        
        mapper = cls.__mapper__
        visible_cols = cls.get_cols('visible')
        visible_keys = cls.get_col_keys('visible')
        pk_tuple = mapper.primary_key
        pk_cols = set(pk_tuple)

        # 基础查询列表包括可见的列和主键列
        query_cols = [col for col in mapper.columns if col in visible_cols | pk_cols]
        
        # 连接查询列表
        joins = []

        # 引用表映射 
        # ref_map = {
        #   引用列名：{
        #       'tablename': 引用表名, 
        #       'pk_names': 引用表主键列名元组
        #    }
        # }
        ref_map = []

        for rel in mapper.relationships:
            if rel.uselist:
                continue
            ref_model = rel.entity.class_
            if hasattr(ref_model, 'name'):
                # 只处理单主键的引用表
                ref_pk_attr = ref_model.__mapper__.primary_key[0]
                ref_name_attr = getattr(ref_model, 'name', None)
                if not (ref_model is None or ref_name_attr is None):
                    ref_dict = dict()
                    ref_dict['ref_name'] = ref_name_attr.name
                    ref_dict['ref_table'] = ref_model.__tablename__
                    ref_dict['ref_pk'] = ref_pk_attr.name
                    ref_map.append(ref_dict)
                    query_cols.append(ref_name_attr.label(ref_name_attr.name))
                    query_cols.append(ref_pk_attr)
                    visible_keys.add(ref_name_attr.name)
                    joins.append(ref_model)
        query = select(*query_cols)
        if joins:
            query = query.join_from(cls, *joins)
        
        datatable = dict()
        
        # 执行查询，在方法开始已经验证过db_session是可用的
        try:
            result = cls.db_session.execute(query) # type: ignore
        except DatabaseError as e:
            raise DatabaseError(f'Invalid query {query} or session {cls.db_session} for {cls}')
        
        datatable['headers'] = tuple(key for key in result.keys() if key in visible_keys)
        datatable['data'] = []
        datatable['_pks'] = []
        datatable['ref_pks'] = []
        datatable['ref_map'] = ref_map
        if not result:
            return datatable  
        
        pk_keys = set(pk.name for pk in pk_tuple)
        
        # json 类型的数据列，只显示可见的列
        json_keys = cls.get_col_keys('DataJson', 'dict')
        datatable['headers_json'] = json_keys - (json_keys - visible_keys)

        for row in result:
            datarow = []
            _pks = []
            for key in result.keys():
                value = row._mapping[key]
                if key in visible_keys:
                    if value is None:
                        value = ''
                    datarow.append(value)
                if key in pk_keys:
                    _pks.append(str(value))
            datatable['data'].append(datarow)
            datatable['_pks'].append(','.join(_pks))
            if ref_map:
                ref_row = []
                _ref_pks = []
                for ref_dict in ref_map:
                    _ref_pks = row._mapping[ref_dict['ref_pk']]
                    ref_row.append(_ref_pks)
                datatable['ref_pks'].append(tuple(ref_row))
        return datatable

    @classmethod
    def fetch_ref_names(cls) -> dict[str, tuple[Any]]:
        """
        :rtype: dict[str, Any]
        :return: dict with key = refereneced column name and 
         value = tuple (referenced column values
         in pre-defined order in `cls.col_key_info['ref_name_order']`)}
        
        .. example::
        { 'entity_name': ('entity_id', 'entity_frequency.desc')}
        """
        if cls._validate_session() is False:
            raise DatabaseError('Invalid db_session {cls.db_session} for {cls}')
        
        ref_names = dict() 
        mapper = cls.__mapper__
        for rel in mapper.relationships:
            if rel.uselist:
                continue
            query = None
            ref_name_attr = None
            ref_model = rel.entity.class_
            if hasattr(ref_model, 'name'):
                ref_name_attr = getattr(ref_model, 'name', None)
                if not (ref_model is None or ref_name_attr is None):
                    query = select(ref_name_attr)
                    ref_name_order = cls.col_key_info.get('ref_name_order', set())
                    if ref_name_order and isinstance(ref_name_order, dict):
                        rno_str_list = ref_name_order.get(ref_name_attr.name, None)
                        if rno_str_list is not None and isinstance(rno_str_list, Iterable):
                            for rno_str in rno_str_list:   
                                if isinstance(rno_str, str):
                                    rno_strs = rno_str.split('.')
                                    if hasattr(ref_model, rno_strs[0]):
                                        len_rno = len(rno_strs)
                                        if len_rno == 1 or (len_rno == 2 and rno_strs[1].lower() == 'asc'):
                                            query = query.order_by(getattr(ref_model, rno_strs[0]))
                                        elif len_rno == 2 and rno_strs[1].lower() == 'desc':
                                            query = query.order_by(getattr(ref_model, rno_strs[0]).desc())
            if ref_name_attr is not None and \
                query is not None and \
                cls.db_session is not None:
                try:
                    ref_col_values = cls.db_session.scalars(query)
                except DatabaseError as e:
                    raise DatabaseError(f'Invalid query {query} \
                        or session {cls.db_session} for {cls}')
                ref_names[ref_name_attr.name] = tuple(ref_col_values)
        return ref_names
