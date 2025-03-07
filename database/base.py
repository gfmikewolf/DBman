# app/database/base.py
import logging
import json
from typing import List, Dict, Tuple, Any
from datetime import date
from enum import Enum
from sqlalchemy import (
    Result, select, Select
)
from sqlalchemy.orm import (
    DeclarativeBase,
    ColumnProperty
)
from sqlalchemy.sql.expression import ColumnClause
from copy import deepcopy
from app.utils.type_tools import convert_string_by_attr_type

class Base(DeclarativeBase):
    # 当前用户可访问的表与数据模型的映射
    map_table_Model: Dict[str, 'Base'] = {}
    """
    hidden: List[ColumnProperty]
    readonly: List[ColumnProperty]
    json_classes: Dict[ColumnProperty, 'JsonBase']
    """
    attr_info: Dict[str, Any] = {
        'hidden': [],
        'readonly': [],
        'json_classes': {}
    }
    @classmethod
    def get_columns(cls, attr_info_keys: Tuple[str,...]) -> List[ColumnProperty]:
        info_keys = list(attr_info_keys)
        columns = []
        for key in info_keys:
            columns.extend(cls.attr_info.get(key, []))
        return columns

    @classmethod
    def query_all(cls, exclude: Tuple[str, ...]=('hidden',), with_ref_attrs: bool=True) -> Select:
        """
        查询所有数据，排除特定信息的列属性，添加关联模型的属性。

        参数:
        exclude (Tuple[str, ...]): 需要排除的列属性，默认为 ('hidden',)。
        with_ref_attrs (bool): 是否添加关联模型的属性，默认为 True。

        返回:
        Select: 一个 SQLAlchemy Select 对象，用于查询数据。
        """
        pk_columns = cls.attr_info.get('pk', [])
        if not pk_columns:
            raise AttributeError('Primary key not defined in {cls} attr_info')
        query_columns = []
        exclude_columns = cls.get_columns(exclude)
        exclude_columns.extend(pk_columns)
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
        query = select(*pk_columns,*query_columns)
        if join_models:
            query = query.select_from(cls)
            for model in join_models:
                query = query.join(model)
        return query
    
    @classmethod
    def query_all_ref_attrs(cls, new_order_by: Dict[ColumnProperty, List[ColumnProperty | ColumnClause]] = {}) -> Dict[ColumnProperty, Select]:
        """
        获取所有关联属性的查询选项。

        该方法生成一个包含所有关联属性查询的字典，每个键是关联属性，
        值是一个 SQLAlchemy Select 对象，用于查询该属性的值。

        参数:
        new_order_by (Dict[ColumnProperty, List[ColumnProperty | ColumnClause]]): 
            一个可选的字典，用于指定新的排序规则。字典的键是关联属性，
            值是一个包含排序列的列表。如果未提供，则使用默认的排序规则。

        返回:
        Dict[ColumnProperty, Select]: 一个字典，其中键是关联属性，值是对应的查询对象。
        """
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

    @classmethod
    def split_result(cls, result: Result, exclude_info: Tuple[str, ...]=('hidden',)) -> Tuple[List[str], List[List[Any]]]:
        """
        从查询结果中分离出主键列和其他列的数据。

        参数:
        result (Result): 查询结果对象。
        exclude (Tuple[str, ...]): 需要排除的列属性，默认为 ('hidden',)。

        返回:
        Tuple[List[str], List[List[Any]]]: 包含主键列和其他列数据的元组。
        """
        pk_attrs = cls.attr_info.get('pk', [])
        pk_keys = [pk_attr.key for pk_attr in pk_attrs]
        if not pk_attrs:
            raise AttributeError('Primary key not defined in {cls} attr_info')

        exclude_columns = cls.get_columns(exclude_info)

        pks = []
        data = []

        for row in result:
            pks = ','.join([str(getattr(row, key)) for key in pk_keys])
            data_row = [getattr(row, col.key) for col in cls.__mapper__.column_attrs if col not in exclude_columns and col not in pk_columns]
            headers.extend([col.key for col in cls.__mapper__.column_attrs if col not in exclude_columns and col not in pk_columns])
            data.append(pk_values + other_values)

        return [', '.join(pk_values)], data

    def update_by_form_data(self, form_data: Dict[str, str]) -> bool:
        """
        用表单数据更新模型实例的数据。如果尝试更新只读属性，或缺失必需属性会抛出异常

        参数:
        form_data (Dict[str, str]): 包含需要更新的数据的字典，其中键是属性名称，值是属性的新值。

        返回:
        bool: 如果更新成功返回 True，否则返回 False。
        """
        readonly_keys = [attr.key for attr in self.attr_info.get('readonly', [])]
        required_keys = [attr.key for attr in self.attr_info.get('required', [])]
        json_classes = self.attr_info.get('json_classes', {})
        original_data = deepcopy(self.__dict__)  # 深拷贝原始数据
        
        try:
            for key, value in form_data.items():
                if key in readonly_keys:
                    raise AttributeError(f'Modifying read-only attribute ({self}{key}) in form update')
                attr = getattr(self, key, None)
                if attr is None:
                    raise AttributeError(f'Attribute {key} not found in Model {self}')
                converted_value = convert_string_by_attr_type(attr, value)
                if converted_value is None:
                    raise AttributeError(f'Type conversion error in Attribute {key} and Value={value}')
                elif key in json_classes.keys():
                    classes_info = json_classes[key]
                    if classes_info.get('identity_on') is None:
                        raise AttributeError(f'Identity attribute not found in json_classes')
                    identity_on = getattr(self, classes_info['identity_on'], None)
                    if identity_on is None:
                        raise AttributeError(f'Identity attribute {classes_info["identity_on"]} not found in Model {self}')
                    identity_attr = classes_info.get('identity_attr', None)
                    if identity_attr is None:
                        raise AttributeError(f'Identity attribute not found in json_classes')
                    identity_value = getattr(identity_on, identity_attr, None)
                    if identity_value is None:
                        raise AttributeError(f'Identity attribute {identity_attr} not found in Model {identity_on}')
                    classes_map = classes_info[identity_on].get('json_classes', {})
                    if not classes_map:
                        raise AttributeError(f'Json classes map not found in {classes_info.identity_on}')
                    json_class = classes_map.get(identity_value, None)
                    if json_class is None:
                        raise AttributeError(f'Json class not found in {classes_map} with key {identity_value}')
                    if not issubclass(json_class, JsonBase):
                        raise AttributeError(f'Json class {json_class} is not subclass of JsonBase')
                    converted_value = json.loads(value, object_hook=json_classes[key].object_hook)
                else:
                    converted_value = None
                if converted_value is None:
                    raise AttributeError(f'Value mismatch in key:{key}, value={value}')
                # 其他类型转换可以在这里添加
                setattr(self, key, converted_value)
                if key in required_keys:
                    required_keys.remove(key)
            if required_keys:
                raise AttributeError(f'Required keys not fully set: required_keys left: {required_keys}')
            return True
        except Exception as e:
            # 恢复原始数据，排除以双下划线开头的内置属性
            self.__dict__.update({k: v for k, v in original_data.items() if not k.startswith('__')})
            logging.error(f"Error in updating {self}. Error: {e}")
            return False

class JsonBase:
    """
    keys均为JsonBase类的属性名
    """
    attr_info: Dict[str, Any] = {
        'data_keys': [],
        'required_keys': [],
        'readonly_keys': []
    }

    @classmethod
    def convert_value_by_attr_type(cls, attr: Any, value: Any) -> Any:
        """
        额外的值类型转换函数，用于复杂的数据类型转换，如字典、列表、类等。
        继承JsonBase的子类有必要的时候需要重载这个方法。
        方法在self.object_hook中在数字、日期格式转换后被调用。

        参数:
        attr (Any): 属性的类型信息。
        value (Any): 需要转换的值。

        返回:
        Any: 转换后的值。
        """
        return value
    
    @classmethod
    def object_hook(cls, obj) -> Dict[str, Any]:
        """
        将表单JSON数据字符串转换为字典，
        如果JSON数据对应的JsonBase模型类必需属性缺失，抛出异常。
        如果JSON数据对应Jsonbase模型类只读属性，则忽略只读属性。
        如果JSON数据有冗余，不会抛出异常，但冗余部分主动进行类型转换

        参数:
        obj (dict): 表单数据的 JSON 字典。

        返回:
        Dict[str, Any]: 转换后的字典，其中包含模型实例的数据。
        """
        data_keys = cls.attr_info.get('data_keys', [])
        required_keys = cls.attr_info.get('required_keys', [])
        readonly_keys = cls.attr_info.get('readonly_keys', [])
        for data_key in data_keys:
            if (data_key in required_keys and data_key not in obj):
                raise AttributeError(f'required attribute {data_key} not found')
            if data_key in readonly_keys:
                continue
            data_attr = getattr(cls, data_key, None)
            if data_attr is None:
                raise AttributeError(f'attr_info corrupted on {data_key}')
            converted_value = convert_string_by_attr_type(data_attr, obj[data_key])
            if converted_value is None:
                raise ValueError(f'Value cannot be converted as expected {data_key}:{obj[data_key]}')
            converted_value = cls.convert_value_by_attr_type(data_attr, converted_value)
            obj[data_key] = converted_value
        return obj
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将模型实例转换为字典。

        返回:
        Dict[str, Any]: 包含模型实例数据的字典。
        """
        data_keys = self.attr_info.get('data_keys', [])
        json_dict = {}
        for key in data_keys:
            attr = getattr(self, key, None)
            if attr is None:
                raise AttributeError(f'Attribute {key} not found in Model {self}')
            if isinstance(attr, date):
                json_dict[key] = attr.strftime('%Y-%m-%d')
            elif isinstance(attr, Enum):
                json_dict[key] = attr.value
            elif isinstance(attr, JsonBase):
                json_dict[key] = attr.to_dict()
            else:
                json_dict[key] = attr
        return json_dict
