from profiteer import config, bpgsql3, cli_f, common_f
import datetime
import re

# Use this to target the mock or production DB
mock_mode = config.get('use_mock_db', False)

alter_default_string = "ALTER TABLE {0} ALTER COLUMN {1} SET DEFAULT '{2}';"
alter_type_string = "ALTER TABLE {0} ALTER COLUMN {1} TYPE {2};"
strip_quotes_re = re.compile(r"(^'|'$)")

try:
    if mock_mode:
        host        = config.get('mock_db_host')
        username    = config.get('mock_db_username')
        password    = config.get('mock_db_password')
        dbname      = config.get('mock_db_name')
    
    else:
        host        = config.get('db_host')
        username    = config.get('db_username')
        password    = config.get('db_password')
        dbname      = config.get('db_name')
    
except KeyError as e:
    # We set all the needed keys to be blank and allow
    # the program to error when making the connection
    
    host        = ""
    username    = ""
    password    = ""
    dbname      = ""
    
    config.init("mock_db_host",       "localhost")
    config.init("mock_db_username",   "username")
    config.init("mock_db_password",   "password")
    config.init("mock_db_name",       "profiteer")
    
    config.init("db_host",            "localhost")
    config.init("db_username",        "username")
    config.init("db_password",        "password")
    config.init("db_name",            "profiteer_mock")
    
    config.init("use_mock_db",            False)
    
    config.save()

except Exception as e:
    raise

def query(cursor, *queries):
    for q in queries:
        if type(q) == list or type(q) == tuple:
            query(cursor, *q)
        else:
            if q[0:2] == "--": continue
            if q.strip() == "": continue
            try: cursor.execute(q)
            except Exception as e:
                raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), q))

def get_custom_cursor(username, password, host, dbname, dictionaries=True):
    try:
        connection = bpgsql3.connect(None, username, password, host, dbname)
    except Exception:
        if username == "" or password == "":
            print(cli_f.shell_text("[r]The database entries in the config.json file are blank[/r]"))
        raise
    
    return connection.cursor(dictionaries)
    
def get_cursor(dictionaries=True):
    return get_custom_cursor(username, password, host, dbname, dictionaries)

def get_mock_cursor():
    return get_custom_cursor(username, password, host, config.get('mock_db_name'), dictionaries=True)

def get_test_cursor():
    return get_custom_cursor(username, password, host, config.get('test_db_name'), dictionaries=True)

def build_default(default_value, escape_func=None, array_count=0):
    # If no escape function, make a pointless function
    if escape_func == None: escape_func = lambda x: x
    
    if array_count == 0:
        if default_value == None:
            return ""
        elif default_value == "":
            return "default ''"
        else:
            return "default '{}'".format(escape_func(default_value))
    elif array_count == 1:
        if default_value == None:
            return ""
        elif type(default_value) in (list, tuple):
            if type(default_value[0]) in (int, float):
                def_string = ",".join([str(escape_func(d)) for d in default_value])
                
                return "default '{{{}}}'".format(def_string)
            else:
                raise Exception("No handler for anything other than arrays of ints or floats")
            
        elif type(default_value) in (int, float):
            return "default '{{{}}}'".format(",".join(["%s" % escape_func(default_value) for i in range(array_count)]))
        else:
            return "default '{{{}}}'".format(",".join(["'%s'" % escape_func(default_value) for i in range(array_count)]))
    else:
        return "default {%s, %s}" % (
            build_default(default_value, escape_func, array_count-1).replace("default ", ""),
            build_default(default_value, escape_func, array_count-1).replace("default ", ""),
        )

def remove_duplicates(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

# A field used in a database
class DBField (object):
    def __init__(self, name, field_type, max_length=None, default="", primary_key=False, foreign_key=(), desc_name="", array=0, is_set=False):
        """
        array: the number of dimensions for an array, set to 0 to leave as non-array field
        is_set: only used if an array, removes duplicate values
        """
        super(DBField, self).__init__()
        self.name           = name
        self.field_type     = field_type
        self.default        = default
        self.max_length     = max_length
        self.primary_key    = primary_key
        self.array          = array
        self.is_set         = is_set
        
        if array > 1:
            raise Exception("Arrays of more than 1 dimension are not currently supported")
        
        if desc_name == "":
            self.desc_name = self.field_type
        else:
            self.desc_name = desc_name
        
        if foreign_key != ():
            self.foreign_table  = foreign_key[0]
            self.foreign_col    = foreign_key[1]
        else:
            self.foreign_table  = ""
            self.foreign_col    = ""
    
    # Ensure the data is of the correct type
    def validate(self, value):
        return value
    
    # Ensure the data will not break a query
    def escape(self, value):
        return value
    
    def create_column(self):
        temp_default = self.default
        if type(self.default) in (list, tuple):
            temp_default = self.default[0]
        
        array = ""
        if self.array > 0:
            array = "".join(["[]" for i in range(self.array)])
        
        if temp_default == None:
            default_str = build_default(self.default, None, self.array)
        
        elif type(temp_default) == str:
            default_str = build_default(self.default, escape, self.array)
        
        elif type(temp_default) == float:
            default_str = build_default(self.default, float, self.array)
            
        elif type(temp_default) == int:
            default_str = build_default(self.default, int, self.array)
            
        elif type(temp_default) == bool:
            default_str = build_default(self.default, bool, self.array)
            
        elif type(temp_default) == datetime.date:
            default_str = build_default(self.default, None, self.array)
        
        elif type(temp_default) == datetime.datetime:
            default_str = build_default(self.default, None, self.array)
        
        else:
            raise Exception("No handler for type %s" % type(self.default))
        
        if self.foreign_col != "" and self.foreign_table != "":
            foreign_str = "REFERENCES {0} ({1})".format(self.foreign_table, self.foreign_col)
        else:
            foreign_str = ""
        return "{name} {data_type}{array} NOT NULL {default} {foreign}".format(
            name = self.name,
            data_type = self.data_type_syntax(),
            default = default_str,
            foreign = foreign_str,
            array = array,
        ).strip()
    
    def check_type(self, db_string, table_info=None):
        """Compares the db_string against what we are
        if needed it will write an ALTER query"""
        raise Exception("{} has not implimented check_type()".format(self.__class__))
    
    def check_default(self, db_string, table_info=None):
        """Compares the db_string against what we are
        if needed it will write an ALTER query"""
        raise Exception("{} has not implimented check_default()".format(self.__class__))
    
    def data_type_syntax(self):
        return self.field_type

class VarcharField (DBField):
    def __init__(self, name, default="", max_length=255, **kwargs):
        kwargs["default"]       = kwargs.get("default", default)
        kwargs["max_length"]    = kwargs.get("max_length", max_length)
        kwargs["desc_name"]     = "character varying"
        super(VarcharField, self).__init__(name, field_type="Varchar", **kwargs)
    
    def data_type_syntax(self):
        return "varchar(%d)" % self.max_length
    
    def escape(self, value):
        if self.array and type(value) in (tuple, list):
            value = "".join(["''%s''" % escape(v) for v in value])
        elif self.array and type(value) == str:
            # return value.replace("\\", "\\\\").replace("'", "''")
            return value.replace("'", "''")
        elif not self.array:
            # return value.replace("\\", "\\\\").replace("'", "''")
            return value.replace("'", "''")
        else:
            raise Exception("")
    
    def validate(self, value):
        if self.array:
            if type(value) == str:
                value = value.replace("{", "").replace("}","").replace("[", "").replace("]","")
                if value == "": return []
                value = [v for v in value.split(",") if v.strip() != ""]
            
            if self.is_set:
                return remove_duplicates(value)
            
            return value
        
        return value
    
    def check_default(self, db_string, table_info=None):
        if self.array:
            return []
        
        db_def = db_string.replace("::character varying", "")
        db_def = strip_quotes_re.sub("", db_def)
        
        if db_def != self.default:
            return [alter_default_string.format(table_info['Name'], self.name, escape(self.default))]
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != self.desc_name:
            if self.array:
                return []
                raise Exception("Cannot handle arrays yet")
            elif db_string == "Array":
                raise Exception("DB says it's an array but it's not")
            
            return [alter_type_string.format(
                table_info['Name'], self.name, self.data_type_syntax()
            )]
        
        return []

class DateField (DBField):
    def __init__(self, name, default="2000-01-01", **kwargs):
        kwargs["default"]       = kwargs.get("default", default)
        super(DateField, self).__init__(name, field_type="date", **kwargs)
    
    def escape(self, value):
        if type(value) == str:
            # return value.replace("\\", "\\\\").replace("'", "''")
            return value.replace("'", "''")
        else:
            return value
    
    def validate(self, value):
        if type(value) == str:
            if len(value.split('/')) == 3: d,m,y = value.split('/')
            if len(value.split('-')) == 3: d,m,y = value.split('-')
            
            try:
                return datetime.date(int(y), int(m), int(d))
            except Exception:
                raise Exception("Could not convert '%s' into datetime" % value)
        
        if type(value) == datetime.date:
            return value
        
        if type(value) == datetime.datetime:
            return datetime.date(value.year, value.month, value.day)
        
        raise Exception("No handler for type %s" % type(value))
    
    def check_default(self, db_string, table_info=None):
        db_def = db_string.replace("::date", "")
        db_def = strip_quotes_re.sub("", db_def)
        
        if db_def != self.default:
            return [alter_default_string.format(table_info['Name'], self.name, escape(self.default))]
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != self.desc_name:
            if self.array:
                raise Exception("Cannot handle arrays yet")
            elif db_string == "Array":
                raise Exception("DB says it's an array but it's not")
            
            return [alter_type_string.format(
                table_info['Name'], self.name, self.data_type_syntax()
            )]
        
        return []
        

class TimestampField (DBField):
    def __init__(self, name, default=datetime.datetime(2000, 1, 1, 0, 0, 0), **kwargs):
        kwargs["default"]       = kwargs.get("default", default)
        super(TimestampField, self).__init__(name, field_type="timestamp without time zone", **kwargs)
    
    def escape(self, value):
        if type(value) == str:
            # return value.replace("\\", "\\\\").replace("'", "''")
            return value.replace("'", "''")
        else:
            return value
    
    def validate(self, value):
        if type(value) == str:
            v = common_f.convert_date(value)
            
            if v == None:
                raise Exception("Could not convert input '{}'".format(value))
            value = v
        
        if type(value) == datetime.datetime:
            return value
        
        if type(value) == datetime.date:
            return datetime.datetime(value.year, value.month, value.day)
        
        if type(value) in (int, float):
            return datetime.datetime.fromtimestamp(value)
        
        raise Exception("No handler for type '{}'" % type(value))
    
    def check_default(self, db_string, table_info=None):
        if type(self.default) == datetime.datetime:
            self_str_default = self.default.strftime("%Y-%m-%d %H:%M:%S")
        else:
            self_str_default = self.default
        
        db_def = db_string.replace("::timestamp without time zone", "")
        db_def = strip_quotes_re.sub("", db_def)
        
        if db_def != self_str_default:
            return [alter_default_string.format(table_info['Name'], self.name, escape(self.default))]
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != self.desc_name:
            if self.array:
                raise Exception("Cannot handle arrays yet")
            elif db_string == "Array":
                raise Exception("DB says it's an array but it's not")
            
            return [alter_type_string.format(
                table_info['Name'], self.name, self.data_type_syntax()
            )]
        
        return []


class TextField (DBField):
    def __init__(self, name, default="", **kwargs):
        kwargs["default"]       = kwargs.get("default", default)
        super(TextField, self).__init__(name, field_type="text", **kwargs)
    
    def escape(self, value):
        return value.replace("'", "''")
        # return value.replace("\\", "\\\\").replace("'", "''")
    
    def check_default(self, db_string, table_info=None):
        db_def = db_string.replace("::text", "")
        db_def = strip_quotes_re.sub("", db_def)
        
        if db_def != self.default:
            return [alter_default_string.format(table_info['Name'], self.name, escape(self.default))]
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != self.desc_name:
            if self.array:
                raise Exception("Cannot handle arrays yet")
            elif db_string == "Array":
                raise Exception("DB says it's an array but it's not")
            
            return [alter_type_string.format(
                table_info['Name'], self.name, self.data_type_syntax()
            )]
        
        return []

class IntegerField (DBField):
    def __init__(self, name, default=0, **kwargs):
        kwargs["default"] = kwargs.get("default", default)
        super(IntegerField, self).__init__(name, field_type="integer", **kwargs)
    
    def validate(self, value):
        if self.array:
            if type(value) == str:
                value = value.replace("{", "").replace("}","").replace("[", "").replace("]","")
                if value == "": return []
                value = [int(v) for v in value.split(",") if v.strip() != ""]
            
            if self.is_set:
                return remove_duplicates(value)
            
            return value
        
        if value == "":
            return 0
        
        return int(value)
    
    def check_default(self, db_string, table_info=None):
        if self.array:
            return []
        
        if type(db_string) == str:
            db_string = db_string.replace("(", "").replace(")", "")
        
        db_def = int(db_string)
        
        if db_def != self.default:
            return [alter_default_string.format(table_info['Name'], self.name, int(self.default))]
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != self.desc_name:
            if self.array:
                return []
                raise Exception("Cannot handle arrays yet")
            elif db_string == "Array":
                raise Exception("DB says it's an array but it's not")
            
            return [alter_type_string.format(
                table_info['Name'], self.name, self.data_type_syntax()
            )]
        
        return []

class DoubleField (DBField):
    def __init__(self, name, default=0, **kwargs):
        kwargs["default"] = kwargs.get("default", default)
        super(DoubleField, self).__init__(name, field_type="double precision", **kwargs)

    def validate(self, value):
        if self.array:
            value = value.replace("{", "").replace("}","")
            if value == "": return []
            value = [float(v) for v in value.split(",") if v.strip() != ""]
            
            if self.is_set:
                return remove_duplicates(value)
            
            return value
        
        if value == "":
            return 0.0
        
        return float(value)
    
    def check_default(self, db_string, table_info=None):
        db_def = db_string.replace("::double precision", "")
        db_def = strip_quotes_re.sub("", db_def)
        
        if self.array:
            return []
        
        db_def = float(db_def)
        
        if db_def != self.default:
            return [alter_default_string.format(table_info['Name'], self.name, float(self.default))]
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != self.desc_name:
            if self.array:
                return []
                raise Exception("Cannot handle arrays yet")
            elif db_string == "Array":
                raise Exception("DB says it's an array but it's not")
            
            return [alter_type_string.format(
                table_info['Name'], self.name, self.data_type_syntax()
            )]
        
        return []

class SerialField (DBField):
    def __init__(self, name, **kwargs):
        kwargs["default"]   = None
        kwargs["desc_name"] = "integer"
        super(SerialField, self).__init__(name, field_type="Serial", **kwargs)

    def validate(self, value):
        return int(value)
    
    # It's a serial field, if we're changing the default/type on this it's probably
    # beyond the help of this library
    def check_default(self, db_string, table_info=None):
        if db_string[0:7] != "nextval":
            raise Exception("Serial field has the wrong default")
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != "integer":
            raise Exception("Serial field has the wrong type")
        
        return []

class BooleanField (DBField):
    def __init__(self, name, **kwargs):
        kwargs["default"] = kwargs.get("default", False)
        super(BooleanField, self).__init__(name, field_type="boolean", **kwargs)
    
    def validate(self, value):
        if type(value) == str:
            return True if value.lower() == "true" else False
        
        else:
            return True if value else False
    
    def check_default(self, db_string, table_info=None):
        db_string = db_string.lower()
        if db_string == "true": db_def = True
        elif db_string == "false": db_def = False
        else:
            raise Exception("Cannot handle db_string value of '{}'".format(db_string))
        
        if db_def != self.default:
            return [alter_default_string.format(table_info['Name'], self.name, bool(self.default))]
        
        return []
    
    def check_type(self, db_string, table_info=None):
        if db_string != self.desc_name:
            if self.array:
                return []
                raise Exception("Cannot handle arrays yet")
            elif db_string == "Array":
                raise Exception("DB says it's an array but it's not")
            
            return [alter_type_string.format(
                table_info['Name'], self.name, self.data_type_syntax()
            )]
        
        return []

# This one is our bread and butter DB class
class DBConnectedObject (object):
    table_info = {
        "Name":         "",
        "Indexes":      (),
        "Fields":       (),
        "Link tables":  (),
    }
    
    """Base class for most classes used in the system"""
    def __init__(self, row = {}, **values):
        for f in self.table_info['Fields']:
            
            # Get the value
            if f.name in row:       v = row[f.name]
            elif f.name in values:  v = values[f.name]
            else:
                if f.default != None:
                    setattr(self, f.name, f.default)
                continue
            
            # Validate it
            v = f.validate(v)
            
            setattr(self, f.name, v)
    
    def __eq__(self, other):
        if other == None:
            return False
        
        try:
            for p in self.table_info["Fields"]:
                if getattr(self, p.name) != getattr(other, p.name):
                    return False
            
            return True
        except Exception:
            raise
    
    def compare(self, other):
        diffs = []
        
        if other == None:
            return False
        
        try:
            for p in self.table_info["Fields"]:
                if getattr(self, p.name) != getattr(other, p.name):
                    diffs.append("%s = %s vs %s" % (p.name, getattr(self, p.name), getattr(other, p.name)))
            
        except Exception:
            raise
        
        return "\n".join(diffs)
    
    def __str__(self):
        output = []
        
        for p in self.table_info["Fields"]:
            output.append("%s: %s" % (p.name, getattr(self, p.name)))
        
        return "\n".join(output)
    
    def get_from_form(self, cursor, form_list):
        """Fill the class up from a form submission"""
        http_dict = {}
        for http_data in form_list:
            http_dict[http_data.name] = http_data.value
        
        self.get_from_dict(cursor, http_dict)
    
    def get_from_dict(self, cursor, form_dict):
        """Fill up the class from a dictionary"""
        # First we need to set every field to None
        for f in self.table_info["Fields"]:
            if f.name in form_dict:
                setattr(self, f.name, f.validate(form_dict[f.name]))
            else:
                setattr(self, f.name, None)
    
    def update(self, cursor=None, test_mode = False):
        """Updates the database, test mode returns the query that will be run rather than running it"""
        fields = []
        primary_keys = []
        for f in self.table_info["Fields"]:
            if hasattr(self, f.name):
                f_value = getattr(self, f.name)
            else:
                continue
            
            if f_value != None:
                f_value = f.validate(f_value)
            else:
                if f.field_type == "boolean":
                    f_value = False
            
            # We don't want to update this, we'll be using it in the where part
            if f.primary_key:
                if f_value == None:
                    raise Exception("Primary key '%s' missing for '%s'" % (f.name, self.table_info['Name']))
                
                primary_keys.append("%s = %s" % (f.name, f_value))
            
            else:
                if f_value != None:
                    if f.field_type in ("Varchar", "text"):
                        if f.array:
                            fields.append("%s = '{%s}'" % (f.name, ",".join(["%s" % escape(v) for v in f_value])))
                            # fields.append("%s = '{%s}'" % (f.name, str(escape(f_value)).replace("[","").replace("]","")))
                        else:
                            fields.append("%s = '%s'" % (f.name, escape(f_value)))
                    else:
                        if f.array:
                            fields.append("%s = '{%s}'" % (f.name, str(f_value).replace("[","").replace("]","")))
                        else:
                            fields.append("%s = '%s'" % (f.name, f_value))
        
        query = "UPDATE %s SET %s WHERE %s;" % (self.table_info['Name'], ",".join(fields), " AND ".join(primary_keys))
        
        if test_mode:
            return [query]
        else:
            try: cursor.execute(query)
            except Exception as e:
                raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
        
    def insert(self, cursor=None, test_mode=False):
        """Inserts the object into the database"""
        
        fields = []
        values = []
        serials = []
        for f in self.table_info["Fields"]:
            # Serials are done automatically
            if type(f) == SerialField:
                serials.append(f)
                continue
            
            f_value = getattr(self, f.name)
            
            # Validation
            if f_value != None:
                f_value = f.validate(f_value)
            else:
                if f.field_type == "boolean":
                    f_value = False
            
            if f_value != None:
                if f.array:                    
                    fields.append('"%s"' % escape(f.name))
                    values.append("'{%s}'" % ",".join([str(f.escape(v)) for v in f_value]))
                else:
                    fields.append('"%s"' % escape(f.name))
                    values.append("'%s'" % f.escape(f_value))
                
            elif f.array:
                fields.append('"%s"' % escape(f.name))
                values.append("'{}'")
        
        query = """INSERT INTO {table_name} ({fields}) VALUES ({values});""".format(
            table_name = self.table_info['Name'],
            fields = ", ".join(fields),
            values = ", ".join(values),
        )
        
        if test_mode:
            return [query]
        else:
            try: cursor.execute(query)
            except Exception as e:
                raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
            
            # At this point we probably don't have an ID, it's time to get one
            if len(serials) > 1:
                raise Exception("No handler for more than 1 serial field")
    
    def delete(self, cursor=None, test_mode=False):
        primary_keys = []
        
        for f in self.table_info["Fields"]:
            # We don't want to update this, we'll be using it in the where part
            if f.primary_key:
                if getattr(self, f.name) == None:
                    raise Exception("Primary key '%s' missing for '%s'" % (f.name, self.table_info['Name']))
                
                primary_keys.append(f.name)
        
        if len(primary_keys) > 1:
            raise Exception("No handler for multiple primary keys")
        else:
            field = primary_keys[0]
            value = getattr(self, field)
            
            query = "DELETE FROM {table_name} WHERE {field} = {value};".format(
                table_name = self.table_info['Name'],
                field = field,
                value = value,
            )
        
        if test_mode:
            return [query]
        else:
            try: cursor.execute(query)
            except Exception as e:
                raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
        
        
def escape(text):
    """Helps to defeat the vile forces of SQL-injection!"""
    return text.replace("'", "''")
    # return text.replace("\\", "\\\\").replace("'", "''")

# http://www.kylev.com/2009/05/22/python-decorators-and-database-idioms/
def try_transaction(func):
    """Wrap a function in an idomatic SQL transaction.  The wrapped function
    should take a cursor as its first argument; other arguments will be
    preserved.
    """
    def new_func(cursor, *args, **kwargs):
        try:
            cursor.execute("BEGIN")
            retval = func(cursor, *args, **kwargs)
            cursor.execute("COMMIT")
        except:
            cursor.execute("ROLLBACK")
            raise
        
        return retval
    
    # Tidy up the help()-visible docstrings to be nice
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    
    return new_func
