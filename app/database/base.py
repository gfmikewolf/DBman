# app/database/base.py

__all__ = ['Base', 'DataJson', 'DataJsonType']

# python
from copy import deepcopy
from math import e
from sqlite3 import DatabaseError
from typing import Any, Iterable, Optional
from enum import Enum # 用到eval('Enum')，需要导入
from datetime import date # 用到eval('date')，需要导入
import json
# sqlalchemy
from sqlalchemy import Column, select, Select
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.orm import DeclarativeBase, Session, ColumnProperty
# app
from app.utils.common import args_to_dict

def serialize_value(attr: Any) -> Any:
    """
    将变量转换为可序列化为存储为JSON的数据类型。可适配ColumnProperty属性。

    参数:
    value (Any): 值。

    返回:
    Any: 序列化后的值。
    """
    
    if isinstance(attr, ColumnProperty):
        attr_type = attr.type.python_type
    else:
        attr_type = type(attr)
    srl_value = None
    if isinstance(attr, set) or isinstance(attr, tuple):
        srl_value = [serialize_value(v) for v in attr]
    elif isinstance(attr, dict):
        srl_value = {k: serialize_value(v) for k,v in attr.items()}
    elif issubclass(attr_type, Enum):
        srl_value = attr.value
    elif attr_type == date:
        srl_value = attr.isoformat()
    elif issubclass(attr_type, DataJson):
        srl_value = attr.data_dict(serializeable=True)
    else:
        srl_value = attr
    return srl_value if srl_value is not None else ''

def convert_value_by_python_type(value: Any, python_type: Any) -> Any:
    """
    根据python类型转换值。

    参数:
    value (Any): 值。
    python_type (Any): Python类型。

    返回:
    Any: 转换后的值。
    """

    if value is None:
        return None
    converted_value = value
    if isinstance(value, python_type):
        return value
    elif issubclass(python_type, date) and isinstance(value, str):
        converted_value = date.fromisoformat(value)
    elif issubclass(python_type, int) and isinstance(value, str):
        converted_value = python_type(value)
    elif issubclass(python_type, float) and (isinstance(value, str) or isinstance(value, int)):
        converted_value = python_type(value)
    elif issubclass(python_type, bool) and (isinstance(value, str) or isinstance(value, int) or isinstance(value, float)): 
        if isinstance(value, str):
            converted_value = value.lower() not in ['false', '0', '', 'none', 'null']
        if isinstance(value, int) or isinstance(value, float):
            converted_value = value != 0
    elif (issubclass(python_type, set) or issubclass(python_type, list)) and isinstance(value, Iterable):
        converted_value = python_type(value)
    elif issubclass(python_type, dict) and (isinstance(value, str) or isinstance(value, DataJson)):
        if isinstance(value, str):
            converted_value = json.loads(value)
        elif isinstance(value, DataJson):
            converted_value = value.data_dict()
    elif issubclass(python_type, DataJson) and (isinstance(value, str) or isinstance(value, dict)):
        converted_value = DataJson.get_obj(value)
    elif issubclass(python_type, Enum) and (isinstance(value, str) or isinstance(value, int)):
        if isinstance(value, str):
            value = value.lower()
        converted_value = python_type(value)
    else:
        raise AttributeError(f'Value {value} ({type(value).__name__}) of wrong format for key: ({python_type.__name__})')
    return converted_value

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

    col_key_info: dict[str, set[str] | dict[str, tuple[str,...]]] = NotImplemented
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
                value = args_dict[key]
                if value is not None:
                    setattr(self, key, value)
       
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
            elif info == 'longtext':
                info_cols = set()
                for str_col in cls.get_cols('str'):
                    if str_col.info.get('longtext', None) is not None:
                        info_cols.add(str_col)
                cols.update(info_cols)
            else:
                info_cols = set()
                for col in cls.__mapper__.columns:
                    if col.info.get(info, None) is not None:
                        info_cols.add(col)
                cols.update(info_cols)
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
    
    def _super_setattr(self, key: str, value: Any) -> None:
        super().__setattr__(key, value)
   
    def data_dict(self, serializeable: bool = False) -> dict[str, Any]:
        data_dict = {'__tablename__': self.__tablename__}
        data_keys = self.get_col_keys('data')
        for data_key in data_keys:
            if not hasattr(self, data_key):
                raise AttributeError(f'Invalid attribute {data_key} for {self}')
            attr = getattr(self, data_key)
            if attr is None:
                data_dict[data_key] = '' if serializeable else None
            else:
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
    def get_ref_list(cls, ref_name_order: dict[str, tuple[str, ...]]) -> list[tuple[str, str]]:
        """
        :return: list of tuple[referenced pk value joined by comma, referenced name column value]
        """
        if Base._validate_session() is False:
            raise DatabaseError('Invalid db_session {cls.db_session}')
        
        query = None
        list_pks_name = []
        ref_model_pks = cls.__mapper__.primary_key
        if not hasattr(cls, 'name'):
            return list_pks_name
        
        query = select(*ref_model_pks, cls.name) # type: ignore
        if ref_name_order is not None and isinstance(ref_name_order, dict):
            order_by_str_tuple = ref_name_order.get(cls.name.name, None) # type: ignore
        if order_by_str_tuple is not None and isinstance(order_by_str_tuple, Iterable):
            for rno_str in order_by_str_tuple:   
                if isinstance(rno_str, str):
                    rno_strs = rno_str.split('.')
                    if hasattr(cls, rno_strs[0]):
                        len_rno = len(rno_strs)
                        if len_rno == 1 or (len_rno == 2 and rno_strs[1].lower() == 'asc'):
                            query = query.order_by(getattr(cls, rno_strs[0]))
                        elif len_rno == 2 and rno_strs[1].lower() == 'desc':
                            query = query.order_by(getattr(cls, rno_strs[0]).desc())
        if query is not None and cls.db_session is not None:
            try:
                result = cls.db_session.execute(query)
            except DatabaseError as e:
                raise DatabaseError(f'Invalid query {query}'
                    f'or session {cls.db_session}') 
                            
            for row in result:
                pk_values = ','.join(map(str, row[:-1]))
                name_value = row[-1]
                row_pks_name = (pk_values, name_value)
                list_pks_name.append(row_pks_name)
        return list_pks_name
    
    @classmethod
    def fetch_col_select_options(cls) -> dict[str, tuple[Any]]:
        """
        :return:
        - key = local column name 
        - value = [tuple[referenced pk value, referenced column value]]
        - values are ordered according to col_key_info['ref_name_order']
        - orderby = { 'entity_name': tuple['entity_id', 'entity_frequency.desc']}
        """
        if Base._validate_session() is False:
            raise DatabaseError('Invalid db_session {cls.db_session}')
        
        col_select_options = dict()
        # Extract foreign key col and referenced pks and name tuple for each relationship
        mapper = cls.__mapper__
        for rel in mapper.relationships:
            if rel.uselist:
                continue
            ref_model = rel.entity.class_
            if not issubclass(ref_model, Base):
                raise AttributeError(f'Invalid ref_model {ref_model} for {cls}')
            ref_name_order = cls.col_key_info.get('ref_name_order', set())
            if not isinstance(ref_name_order, dict):
                raise AttributeError(f'Invalid ref_name_order {ref_name_order} for {cls}')
            list_pks_name = ref_model.get_ref_list(ref_name_order)
            col_select_options[next(iter(rel.local_columns)).name] = list_pks_name
        
        # Extract Enum types and get options from Enum definition
        enum_cols = cls.get_cols('Enum')
        for col in enum_cols:
            enum_cls = col.type.python_type
            values = [(member.value, member.value) for member in enum_cls] # type: ignore enum_cls is subclass of Enum
            col_select_options[col.name] = values        
        return col_select_options
    
    @classmethod
    def fetch_datajson_ref_map(cls) -> dict[str, str]:
        """
        :return: dict {local_col.name: datajson_id_col.name }
        """
        datajson_cols = cls.get_cols('DataJson')
        datajson_id_cols = cls.get_cols('DataJson_id_for')
        datajson_ref_map = dict()
        for dj_col in datajson_cols:
            found = False
            for id_col in datajson_id_cols:
                id = id_col.info.get('DataJson_id_for', None)
                if id and id == dj_col.name:
                    datajson_ref_map[dj_col.name] = id_col.name
                    found = True
            if found == False:
                raise AttributeError(f'{cls}.{dj_col.name} is a class derived from DataJson, but its identity col is not found in the same model')
        return datajson_ref_map

class DataJsonType(TypeDecorator):
    """
    JsonBase类修饰器，转换类实例与Json字符串
    """
    impl = JSON
    cache_ok = True

    @property
    def python_type(self):
        return DataJson

    # 将DataJson类通过自有dumps()方法转换为字符串
    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.dumps()
        return value

    # 将DataJson字符串通过自有get_obj()方法转换为类
    def process_result_value(self, value, dialect):
        if value is not None:
            return DataJson.get_obj(value)
        return value

class DataJson:
    """
    JSON数据模型基类，用于定义JSON数据模型的基本属性和方法。
    - 类属性:
        - __datajson_id__ (str): 模型类的类型id，子类必须实例化这个属性。
        - class_map (dict[str, type['DataJson']]): 模型类的映射。
        - attr_info (dict[str, Any]): 模型类的属性信息。
    
    公共方法：
        - 类方法:
            - load(data: dict | str | None = None, **kwargs) -> dict[str, Any]: 将JSON字符串或字典转换为字典。
            - get_cls_from_dict(data: dict[str, Any]) -> type['DataJson'] | None: 根据字典获取模型类。
            - convert_value_by_attr_type(value: Any, attr_key: str) -> Any: 根据属性类型转换值。
            - get_keys(*args: str) -> set[str]: 获取包含指定信息的属性的键集合。
            - get_obj(data: str | dict, **kwargs: Any) -> Optional['DataJson']: 获取JSON数据的DataJson类实例。
        - 实例方法:
            - __init__(self, data: str | dict | None = None, **kwargs): 初始化模型实例。
            - dumps(self) -> str: 将模型实例转换为JSON字符串。
            - data_dict(self, serializeable: bool = False) -> dict[str, Any]:
    
    私有方法：
        - 类方法:
            - _load_dict(cls, data: dict) -> dict[str, Any]: 将字典中对应attr_info里'data'类型的数据按类属性进行数据类型转换。
    """
    __datajson_id__ = NotImplemented
    """
    模型类的类型，str类型
    
    类型示例:
    - 'data_json'：基本父类
    - 'clause_entity'：合同实体条款
    - 'clause_scope'：合同范围条款
    - 'clause_expiry': 合同到期条款
    """

    class_map: dict[str, type['DataJson']] = {}
    """
    模型类的映射，dict类型，建议在DataJson类使用前定义该变量

    映射示例:
    - {
        'base': DataJson,
        'entity': ClauseEntity,
        'scope': ClauseScope,
        'expiry': ClauseExpiry
    }
    """

    attr_info: dict[str, Any] = NotImplemented
    """
    模型类的属性信息，dict类型，建议在DataJson类使用前定义该变量

    必需的属性信息:
    - data: 需要存储的数据属性: str

    可选的属性信息
    - required: 必需赋值的属性: str
    - readonly: 只读属性: str
    - hidden: 不需要显示给用户的属性: str
    - foreignkeys: 外键信息: dict
        - ref_table: 引用的数据表名称: str, 如 'contract'
        - ref_pk: 引用的数据库模型键: tuple[str,...] 如 ('contract_id',)
        - ref_name: 引用的数据库模型表征名称: str, 如 'contract_name'
        - order_by: 作为列表框供用户选择时选项的排序要求: tuple[str, ...] 如 ('contract_name', 'contract_fullname.desc')
    """
    def __init__(self, data: str | dict | None = None, **kwargs):
        data_dict = self.load(data, **kwargs)
        self.__dict__.update(data_dict)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.attr_info is NotImplemented:
            cls.attr_info = dict()

    @classmethod
    def load(cls, data: dict | str | None = None, **kwargs) -> dict[str, Any]:
        """
        将JSON字符串或字典转换为字典。

        参数:
        data (dict | str | None): JSON字符串或字典。

        返回:
        dict[str, Any]: 转换后的字典。
        """
        from app.utils import args_to_dict
        args_dict = args_to_dict(data, **kwargs)
        data_json_cls = cls.get_cls_from_dict(args_dict)

        if  data_json_cls is None:
            raise AttributeError('Invalid data: {data} kwargs:{kwargs} to match {json_cls}')

        if not args_dict:
            return args_dict
        else:
            return data_json_cls._load_dict(args_dict)
    
    def dumps(self) -> str:
        """
        将模型实例转换为JSON字符串。

        返回:
        str: 转换后的JSON字符串。
        """
        return json.dumps(self.data_dict(serializeable=True))
    
    @classmethod
    def get_cls_from_dict(cls, data: dict[str, Any]) -> type['DataJson'] | None:
        if cls.__datajson_id__ is NotImplemented:
            datajson_id = data.get('__datajson_id__', None)
            data_json_cls = cls.class_map.get(datajson_id, None)
            if data_json_cls is None:
                raise AttributeError(f'Invalid {datajson_id} in class_map {cls.class_map}')
        else:
            datajson_id = 'data_json'
            data_json_cls = cls
        
        required_keys = data_json_cls.get_keys('required')
        # 找到required_keys中不存在于data.keys()的键
        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise AttributeError(f'Missing required keys: {missing_keys} in {data}')
        
        # 如果data_keys中有readonly的键，抛出属性异常
        readonly_keys = data_json_cls.get_keys('readonly')
        # 如果data_keys中有readonly_keys,下面的计算会得到非空集合
        if (readonly_keys - (readonly_keys - data.keys())):
            raise AttributeError(f'Readonly keys: {readonly_keys} in {data}')
        return data_json_cls

    @classmethod
    def _load_dict(cls, data: dict) -> dict[str, Any]:   
        """
        将字典中对应attr_info里'data'类型的数据按类属性进行数据类型转换。
        - 字典必须经过get_cls_from_dict()方法处理后才能调用该方法。

        参数:
        data (dict): 原始数据。

        返回:
        dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        data_json_cls = cls
        if cls.__datajson_id__ == NotImplemented:
            data_json_cls = cls.get_cls_from_dict(data)
            if data_json_cls is None:
                raise AttributeError(f'Invalid data: {data} to match {data_json_cls}')
        data_dict = {}
        data_dict['__datajson_id__'] = data_json_cls.__datajson_id__
        mod_keys = data_json_cls.get_keys('modifiable')

        for key in mod_keys:
            value = data.get(key, None)
            if value is not None:
                data_dict[key] = data_json_cls.convert_value_by_attr_type(value, key) # type: ignore
        return data_dict

    @classmethod
    def convert_value_by_attr_type(cls, value: Any, attr_key: str) -> Any:
        """
        根据属性类型转换值。如果value不在data_keys中，不进行转换。

        参数:
        attr_key (str): 属性键。
        value (Any): 属性值。

        返回:
        Any: 转换后的属性值。
        """

        attr = getattr(cls, attr_key, None)
        if attr is None:
            raise AttributeError(f'Attribute {attr_key} not found in {cls}')
        attr_type = type(attr)
        converted_value = convert_value_by_python_type(value, attr_type)    
        return converted_value
    
    def data_dict(self, serializeable: bool = False) -> dict[str, Any]:
        """
        将模型实例转换为字典。

        参数:
        serializeable (bool): 是否将值序列化以便存储为JSON。

        返回:
        dict[str, Any]: 包含模型实例数据的字典。
        """

        data_keys = self.get_keys('data')
        if self.__datajson_id__ is NotImplemented:
            djid = 'data_json'
        else:
            djid = self.__datajson_id__
        data_dict = {'__datajson_id__': djid}
        for key, value in self.__dict__.items():
            if key in data_keys:
                attr = getattr(self, key, None)
                if attr is not None:
                    data_dict.update({key: serialize_value(value) if serializeable else value})
        return data_dict
    
    @classmethod
    def get_obj(cls, data: str | dict, **kwargs: Any) -> Optional['DataJson']:
        """
        获取JSON数据的DataJson类实例。

        参数:
        data (str | dict): JSON数据，可以是字符串或字典。
        default (Any): 默认值。

        返回:
        DataJson: 任何继承了DataJson的类实例。
        """
        from app.utils import args_to_dict
        data_dict = args_to_dict(data, **kwargs)
        if not data_dict:
            return None
        
        if cls.__datajson_id__ is NotImplemented:
            datajson_id = data_dict.get('__datajson_id__', None)
            if datajson_id is None:
                raise TypeError(f'__datajson_id__ not found in jsonData: {data}')
            data_json_cls = cls.class_map.get(datajson_id, None)
            if data_json_cls is None:
                raise AttributeError(f'json_cls not found in class_map of {cls} for __datajson_id__: {datajson_id}')
        else:
            data_json_cls = cls

        return data_json_cls(data_dict)

    @classmethod
    def get_keys(cls, *args: str) -> set[str]:
        """
        获取包含指定信息的属性的键集合。
        
        参数:
        *args (str): 包含的信息字符串参数。
        
        返回:
        set[str]: 包含指定信息的键集合。
        """
        keys = set()
        for info in args:
            # 如果已经缓存了信息，返回缓存信息
            if info in cls.attr_info:
                keys.update(cls.attr_info[info])
            # 如果没有缓存信息，根据参数获取信息并缓存
            elif info in {'readonly', 'hidden', 'required', 'data', 'foreignkeys', 'longtext'}:
                info_keys = cls.attr_info.get(info, set())
                keys.update(info_keys)
            elif info == 'modifiable':
                info_keys = cls.get_keys('data') - cls.get_keys('readonly')
                cls.attr_info[info] = info_keys
                keys.update(info_keys)
            elif info == 'visible':
                info_keys = cls.get_keys('data') - cls.get_keys('hidden')
                cls.attr_info[info] = info_keys
                keys.update(info_keys)
            elif info in {'date', 'json', 'int', 'float', 'bool', 'set', 'list', 'dict', 'str', 'DataJson', 'Enum'}:
                info_keys = set()
                for data_key in cls.get_keys('data'):
                    attr = getattr(cls, data_key, None) # type: ignore
                    if attr is None:
                        raise AttributeError(f'Attribute {data_key} not found in {cls}')
                    if isinstance(attr, eval(info)):
                        info_keys.add(data_key)
                cls.attr_info[info] = info_keys
                keys.update(info_keys)  
            else:
                raise AttributeError(f'Invalid key info {info} for {cls}')
        return keys

    @classmethod
    def fetch_datajson_select_options(cls) -> dict[str, tuple[str, str]]:
        options = dict()
        if cls.__datajson_id__ == NotImplemented:
            raise AttributeError('Cannot call fetch_datajson_select_options() on DataJson')
        foreign_keys = cls.get_keys('foreignkeys')
        if foreign_keys: 
            if not isinstance(foreign_keys, dict):
                raise AttributeError(f'Invalid foreignkeys {foreign_keys} for {cls}')
            for fk, ref_table in foreign_keys.items():
                Model = Base.model_map[ref_table]
                ref_list = Model.get_ref_list(cls.attr_info.get('ref_name_order', None))
                options[fk] = ref_list
        for enum_key in cls.get_keys('Enum'):
            enum_attr = getattr(cls, enum_key, None)
            if enum_attr is None:
                raise AttributeError(f'Attribute {enum_key} not found in {cls}')
            enum_cls = type(enum_attr)
            if not issubclass(enum_cls, Enum):
                raise AttributeError(f'Invalid Enum {enum_cls} for {cls}')
            options[enum_key] = [(member.value, member.value) for member in enum_cls]
        return options

    @classmethod
    def get_structure(cls) -> dict[str, Any]:
        struct = dict()
        if cls == DataJson:
            raise AttributeError('Cannot call get_structure() on DataJson')
        
        struct['__datajson_id__'] = cls.__datajson_id__
        struct['data'] = cls.get_keys('data')
        struct['required'] = cls.get_keys('required')
        struct['readonly'] = cls.get_keys('readonly')
        struct['date'] = cls.get_keys('date')
        struct['Enum'] = cls.get_keys('Enum')
        struct['foreignkeys'] = cls.get_keys('foreignkeys')
        struct['longtext'] = cls.get_keys('longtext')
        struct['ref_map'] = cls.fetch_datajson_select_options()

        return struct
  
