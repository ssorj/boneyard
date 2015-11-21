import pickle

from datetime import datetime
from psycopg2 import TimestampFromTicks
from util import *

class SqlType(object):
    def __init__(self, literal, python_type):
        self.literal = literal
        self.python_type = python_type

    def adapt_value(self, value):
        return value

class TimestampType(SqlType):
    def adapt_value(self, value):
        if value is not None:
            return TimestampFromTicks(value / 1000000000)

class PickledType(SqlType):
    def adapt_value(self, value):
        if value is not None:
            return pickle.dumps(value)

class StringIdType(SqlType):
    def adapt_value(self, value):
        if value is not None:
            return str(value)

sql_bool = SqlType("bool", bool)
sql_float4 = SqlType("float4", float)
sql_float8 = SqlType("float8", float)
sql_int2 = SqlType("int2", long)
sql_int4 = SqlType("int4", long)
sql_int8 = SqlType("int8", long)
sql_uint8 = SqlType("numeric(19)", long)
sql_serial4 = SqlType("serial4", long)
sql_serial8 = SqlType("serial8", long)
sql_text = SqlType("text", str)
sql_timestamp = TimestampType("timestamp", datetime)

sql_pickled_map = PickledType("text", dict)
sql_string_id = StringIdType("text", str)

__mappings = (
    (sql_bool, 11, "bool"),
    (sql_float4, 12, "float"),
    (sql_float8, 13, "double"),
    (sql_int2, 1, "count8"),
    (sql_int2, 1, "hilo8"),
    (sql_int2, 1, "uint8"),
    (sql_int2, 16,"int8"),
    (sql_int2, 17, "int16"),
    (sql_int4, 18, "int32"),
    (sql_int4, 2, "count16"),
    (sql_int4, 2, "hilo16"),
    (sql_int4, 2, "uint16"),
    (sql_int8, 19, "int64"),
    (sql_int8, 3, "count32"),
    (sql_int8, 3, "hilo32"),
    (sql_int8, 3, "mma32"),
    (sql_int8, 3, "uint32"),
    (sql_pickled_map, 15, "map"),
    (sql_string_id, 10, "objId"),
    (sql_string_id, 14, "uuid"),
    (sql_text, 6, "sstr"),
    (sql_text, 7, "lstr"),
    (sql_timestamp, 8, "absTime"),
    (sql_uint8, 4, "count64"),
    (sql_uint8, 4, "hilo64"),
    (sql_uint8, 4, "mma64"),
    (sql_uint8, 4, "mmaTime"),
    (sql_uint8, 4, "uint64"),
    (sql_uint8, 9, "deltaTime"),
    )

sql_types_by_qmf_type_code = dict([(x[1], x[0]) for x in __mappings])
sql_types_by_qmf_type_string = dict([(x[2], x[0]) for x in __mappings])
qmf_type_code_by_string = dict([(x[2], x[1]) for x in __mappings])
