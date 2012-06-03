import unittest
import datetime
from profiteer import database_f, common_f, sync_f
from profiteer.test_lib import gui_test_utils
import time

class FakeConnected (database_f.DBConnectedObject):
    table_info = {
        "Name":         "fake_connected",
        "Indexes":      {},
        "Fields":       (
            database_f.SerialField("s1",            primary_key=True),
            
            database_f.VarcharField("v1",           default="v1"),
            database_f.VarcharField("v2",           default="v2"),
            
            database_f.IntegerField("i1",           default=1),
            database_f.IntegerField("i2",           default=2),
            
            database_f.TextField("t1",              default="t1"),
            database_f.TextField("t2",              default="t2"),
            
            database_f.DoubleField("d1",            default=1.1),
            database_f.BooleanField("b1",           default=True),
            
            database_f.IntegerField("afield",       array=True),
            database_f.IntegerField("bfield",       array=True, default=[1,2]),
            
            database_f.DateField("date_field",      default="2000-10-30"),
            database_f.TimestampField("time_field", default="2000-10-30 12:50:59"),
        ),
    }

fake_info = FakeConnected.table_info

class Database_tester (unittest.TestCase):
    test_targets = [
        # Cannot be tested really but it'll quickly become
        # apparent if they don't work
        database_f.query,
        database_f.get_custom_cursor,
        database_f.get_cursor,
        database_f.get_mock_cursor,
        database_f.get_test_cursor,
    ]
    
    maxDiff = None
        
    def test_build_array_default(self):
        self.test_targets.append(database_f.build_default)
        vals = (
            # Default value, escape, array_count
            # Non-arrays
            ("",    None,               0,  "default ''"),
            
            # Arrays
            (None,  database_f.escape,  1,  ""),
            ("",    database_f.escape,  1,  "default '{''}'"),
            ("A",   database_f.escape,  1,  "default '{'A'}'"),
            (1,     None,               1,  "default '{1}'"),
            
            # 2D Arrays
            # ("A", database_f.escape, 2, "default '{{''A''}, {''A''}}'"),
        )
        
        for default_value, escape_func, array_count, expected in vals:
            self.assertEqual(database_f.build_default(default_value, escape_func, array_count), expected)
    
    escape_vals = (
        ("abc", "abc"),
        ("abc'd", "abc''d"),
        ("abc\\'d", "abc\\\\''d"),
    )
    
    def test_escape(self):
        self.test_targets.append(database_f.escape)
        
        for str_in, expected in self.escape_vals:
            self.assertEqual(database_f.escape(str_in), expected)
    
    def test_remove_duplicates(self):
        self.test_targets.append(database_f.remove_duplicates)
        vals = (
            ([1,2,2], [1,2]),
            ([2,1,2], [2,1]),
            ([2,1,3], [2,1,3]),
        )
        
        for list_in, expected in vals:
            self.assertEqual(database_f.remove_duplicates(list_in), expected)
    
    def test_try_transaction(self):
        self.test_targets.append(database_f.try_transaction)
        cursor = database_f.get_test_cursor()
        
        # Set it all up
        results = []
        original_execute = cursor.execute
        cursor.execute = results.append
        
        def without_try(c):
            c.execute("without_try")
        
        @database_f.try_transaction
        def with_try(c):
            c.execute("with_try")
        
        @database_f.try_transaction
        def with_try_execption(c):
            c.execute("with_try_execption")
            raise Exception("")
        
        # Now we make it fall over
        without_try(cursor)
        with_try(cursor)
        
        try:
            with_try_execption(cursor)
        except Exception:
            pass
        
        self.assertEqual(results, [
            "without_try",
            
            "BEGIN",
            "with_try",
            "COMMIT",
            
            "BEGIN",
            "with_try_execption",
            "ROLLBACK",
        ])
        
        cursor.execute = original_execute
    
    def test_DBConnectedObject_creation(self):
        self.test_targets.append(database_f.DBConnectedObject.__eq__)
        self.test_targets.append(database_f.DBConnectedObject.__str__)
        self.test_targets.append(database_f.DBConnectedObject.compare)
        self.test_targets.append(database_f.DBConnectedObject.get_from_form)
        self.test_targets.append(database_f.DBConnectedObject.get_from_dict)
        
        f1 = FakeConnected({
            "s1":   1,
            "v1":   "abc",
            "v2":   "xyz",
            "i1":   1,
            "i2":   2,
            "t1":   "abc abc",
            "t2":   "xyz xyz",
            
            "d1":   1.1,
            "b1":   False,
            
            "afield":   [1,2,3],
            "bfield":   [1,2,3],
            
            # This uses strings
            "date_field":   common_f.convert_date("08-01-1999"),
            "time_field":   common_f.convert_date("08-01-1999 04:05:06"),
        })
        
        f2 = FakeConnected({
            "s1":   2,
            "v1":   "zabc",
            "v2":   "zxyz",
            "i1":   3,
            "i2":   4,
            "t1":   "zabc abc",
            "t2":   "zxyz xyz",
            
            "d1":   1.2,
            "b1":   True,
            
            "afield":   [4,2,3],
            "bfield":   [1,2,3],
            
            # This uses strings too
            "date_field":   common_f.convert_date("20-02-2000"),
            "time_field":   common_f.convert_date("20-02-2000 23:59:59"),
        })
        
        gui_test_utils.new_cgi_form((
            ("s1",   2),
            ("v1",   "zabc"),
            ("v2",   "zxyz"),
            ("i1",   3),
            ("i2",   4),
            ("t1",   "zabc abc"),
            ("t2",   "zxyz xyz"),
            
            ("d1",   1.2),
            ("b1",   True),
            
            ("afield",   "[4,2,3]"),
            ("bfield",   "[1,2,3]"),
            
            # This convets strings
            ("date_field",   datetime.date(2000, 2, 20)),
            ("time_field",   datetime.datetime(year=2000, month=2, day=20, hour=23, minute=59, second=59)),
        ))
        
        f3 = FakeConnected()
        f3.get_from_form(cursor=None, form_list=common_f.cgi_form.list)
        
        # Test __eq__
        self.assertNotEqual(f1, f2)
        if f2 != f3:
            print(f2.compare(f3))
            self.assertEqual(f2, f3)
        
        # Test __str__
        self.assertEqual(str(f1), """s1: 1
v1: abc
v2: xyz
i1: 1
i2: 2
t1: abc abc
t2: xyz xyz
d1: 1.1
b1: False
afield: [1, 2, 3]
bfield: [1, 2, 3]
date_field: 1999-01-08
time_field: 1999-01-08 04:05:06""")
        
        self.assertEqual(str(f2), """s1: 2
v1: zabc
v2: zxyz
i1: 3
i2: 4
t1: zabc abc
t2: zxyz xyz
d1: 1.2
b1: True
afield: [4, 2, 3]
bfield: [1, 2, 3]
date_field: 2000-02-20
time_field: 2000-02-20 23:59:59""")
        
        self.assertEqual(str(f3), str(f2))
        
        # Test compare
        self.assertEqual(f2.compare(f3), "")
        self.assertEqual(f1.compare(f2), """s1 = 1 vs 2
v1 = abc vs zabc
v2 = xyz vs zxyz
i1 = 1 vs 3
i2 = 2 vs 4
t1 = abc abc vs zabc abc
t2 = xyz xyz vs zxyz xyz
d1 = 1.1 vs 1.2
b1 = False vs True
afield = [1, 2, 3] vs [4, 2, 3]
date_field = 1999-01-08 vs 2000-02-20
time_field = 1999-01-08 04:05:06 vs 2000-02-20 23:59:59""")
        
    def test_DBConnectedObject_queries(self):
        self.test_targets.append(database_f.DBConnectedObject.insert)
        self.test_targets.append(database_f.DBConnectedObject.update)
        self.test_targets.append(database_f.DBConnectedObject.delete)
        
        # First we insert it
        fc = FakeConnected({
            "s1":   1,
            "v1":   "abc",
            "v2":   "xyz",
            "i1":   1,
            "i2":   2,
            "t1":   "abc abc",
            "t2":   "xyz xyz",
            
            "b1":   True,
            
            "afield":   [1,2,3],
            "bfield":   [1,2,3],
            
            "date_field":   common_f.convert_date("01-08-1999"),
            "time_field":   common_f.convert_date("01-08-1999 04:05:06"),
        })
        
        self.assertEqual(fc.insert(test_mode=True), [
            'INSERT INTO fake_connected ("v1", "v2", "i1", "i2", "t1", "t2", "d1", "b1", "afield", "bfield", "date_field", "time_field") VALUES (\'abc\', \'xyz\', \'1\', \'2\', \'abc abc\', \'xyz xyz\', \'1.1\', \'True\', \'{1,2,3}\', \'{1,2,3}\', \'1999-08-01\', \'1999-08-01 04:05:06\');'
        ])
        
        # Now we update it
        fc.v1 = "zzz"
        self.assertEqual(fc.update(test_mode=True), [
            "UPDATE fake_connected SET v1 = 'zzz',v2 = 'xyz',i1 = '1',i2 = '2',t1 = 'abc abc',t2 = 'xyz xyz',d1 = '1.1',b1 = 'True',afield = '{1, 2, 3}',bfield = '{1, 2, 3}',date_field = '1999-08-01',time_field = '1999-08-01 04:05:06' WHERE s1 = 1;"
        ])
        
        # Test for partial update
        del(fc.i1)
        del(fc.i2)
        del(fc.t1)
        del(fc.t2)
        del(fc.d1)
        del(fc.afield)
        del(fc.bfield)
        del(fc.b1)
        del(fc.date_field)
        del(fc.time_field)
        self.assertEqual(fc.update(test_mode=True), [
            "UPDATE fake_connected SET v1 = 'zzz',v2 = 'xyz' WHERE s1 = 1;"
        ])
        
        # Finally we kill it
        self.assertEqual(fc.delete(test_mode=True), [
            'DELETE FROM fake_connected WHERE s1 = 1;'
        ])

    def test_check_type(self):
        self.test_targets.extend([
            
            database_f.DBField.data_type_syntax,
            database_f.VarcharField.data_type_syntax,
            
            database_f.DBField.check_type,
            database_f.BooleanField.check_type,
            database_f.DateField.check_type,
            database_f.DoubleField.check_type,
            database_f.IntegerField.check_type,
            database_f.SerialField.check_type,
            database_f.TextField.check_type,
            database_f.TimestampField.check_type,
            database_f.VarcharField.check_type,
        ])
        cursor = database_f.get_test_cursor()
        
        # We actually want to make our table
        sync_f.check_table(cursor, fake_info, fix=True)
        
        # Use this query to grab info about the rows
        db_info_dict = {}
        
        query = """SELECT data_type, column_name FROM INFORMATION_SCHEMA.COLUMNS where table_name = 'fake_connected'"""
        try: cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
        for row in cursor:
            db_info_dict[row['column_name']] = row['data_type']
        
        # BooleanField
        the_field = database_f.BooleanField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['b1'], fake_info), [])
        self.assertEqual(the_field.check_type(db_info_dict['v1'], fake_info),
            ["ALTER TABLE fake_connected ALTER COLUMN the_field TYPE boolean;"]
        )
        
        # DateField
        the_field = database_f.DateField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['date_field'], fake_info), [])
        self.assertEqual(the_field.check_type(db_info_dict['v1'], fake_info),
            ["ALTER TABLE fake_connected ALTER COLUMN the_field TYPE date;"]
        )
        
        # DoubleField
        the_field = database_f.DoubleField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['d1'], fake_info), [])
        self.assertEqual(the_field.check_type(db_info_dict['v1'], fake_info),
            ["ALTER TABLE fake_connected ALTER COLUMN the_field TYPE double precision;"]
        )
        
        # IntegerField
        the_field = database_f.IntegerField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['i1'], fake_info), [])
        self.assertEqual(the_field.check_type(db_info_dict['v1'], fake_info),
            ["ALTER TABLE fake_connected ALTER COLUMN the_field TYPE integer;"]
        )
        
        # SerialField
        the_field = database_f.SerialField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['s1'], fake_info), [])
        self.assertRaises(Exception, the_field.check_type, (db_info_dict['v1'], fake_info))
        
        # TextField
        the_field = database_f.TextField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['t1'], fake_info), [])
        self.assertEqual(the_field.check_type(db_info_dict['v1'], fake_info),
            ["ALTER TABLE fake_connected ALTER COLUMN the_field TYPE text;"]
        )
        
        # TimestampField
        the_field = database_f.TimestampField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['time_field'], fake_info), [])
        self.assertEqual(the_field.check_type(db_info_dict['v1'], fake_info),
            ["ALTER TABLE fake_connected ALTER COLUMN the_field TYPE timestamp without time zone;"]
        )
        
        # VarcharField
        the_field = database_f.VarcharField("the_field")
        self.assertEqual(the_field.check_type(db_info_dict['v1'], fake_info), [])
        self.assertEqual(the_field.check_type(db_info_dict['i1'], fake_info),
            ["ALTER TABLE fake_connected ALTER COLUMN the_field TYPE varchar(255);"]
        )
        
        # Drop it incase it affects any other tests
        try:
            cursor.execute("DROP TABLE fake_connected")
        except Exception:
            pass
    
    def test_check_default(self):
        self.test_targets.extend([
            database_f.DBField.data_type_syntax,
            database_f.VarcharField.data_type_syntax,
            
            database_f.DBField.check_default,
            database_f.BooleanField.check_default,
            database_f.DateField.check_default,
            database_f.DoubleField.check_default,
            database_f.IntegerField.check_default,
            database_f.SerialField.check_default,
            database_f.TextField.check_default,
            database_f.TimestampField.check_default,
            database_f.VarcharField.check_default,
        ])
        
        cursor = database_f.get_test_cursor()
        
        # We actually want to make our table
        sync_f.check_table(cursor, fake_info, fix=True)
        
        # Use this query to grab info about the rows
        db_info_dict = {}
        
        query = """SELECT column_default, column_name FROM INFORMATION_SCHEMA.COLUMNS where table_name = 'fake_connected'"""
        try: cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
        for row in cursor:
            db_info_dict[row['column_name']] = row['column_default']
        
        # Have one correct and one incorrect default to ensure it's not replacing the correct ones
        
        # BooleanField
        self.assertEqual(database_f.BooleanField("the_field", default=False).check_default(
            db_info_dict['b1'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT 'False';"])
        self.assertEqual(database_f.BooleanField("the_field", default=True).check_default(
            db_info_dict['b1'], fake_info
        ), [])
        
        # DateField
        self.assertEqual(database_f.DateField("the_field",  default="1000-01-01").check_default(
            db_info_dict['date_field'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT '1000-01-01';"])
        self.assertEqual(database_f.DateField("the_field", default="2000-10-30").check_default(
            db_info_dict['date_field'], fake_info
        ), [])
        
        # DoubleField
        self.assertEqual(database_f.DoubleField("the_field",  default=1.5).check_default(
            db_info_dict['d1'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT '1.5';"])
        self.assertEqual(database_f.DoubleField("the_field", default=1.1).check_default(
            db_info_dict['d1'], fake_info
        ), [])
        
        # IntegerField
        self.assertEqual(database_f.IntegerField("the_field",  default=5).check_default(
            db_info_dict['i1'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT '5';"])
        self.assertEqual(database_f.IntegerField("the_field", default=1).check_default(
            db_info_dict['i1'], fake_info
        ), [])
        self.assertEqual(database_f.IntegerField("the_field",  default=-1).check_default(
            db_info_dict['i1'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT '-1';"])
        
        # SerialField
        self.assertEqual(database_f.SerialField("the_field",  default=5).check_default(
            db_info_dict['s1'], fake_info
        ), [])
        self.assertEqual(database_f.SerialField("the_field", default=1).check_default(
            db_info_dict['s1'], fake_info
        ), [])
        
        # TextField
        self.assertEqual(database_f.TextField("the_field",  default='tt').check_default(
            db_info_dict['t1'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT 'tt';"])
        self.assertEqual(database_f.TextField("the_field", default='t1').check_default(
            db_info_dict['t1'], fake_info
        ), [])
        
        # TimestampField
        self.assertEqual(database_f.TimestampField("the_field",  default='2012-1-5 10:00:00').check_default(
            db_info_dict['time_field'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT '2012-1-5 10:00:00';"])
        self.assertEqual(database_f.TimestampField("the_field", default='2000-10-30 12:50:59').check_default(
            db_info_dict['time_field'], fake_info
        ), [])
        
        # VarcharField
        self.assertEqual(database_f.VarcharField("the_field",  default='vvv').check_default(
            db_info_dict['v1'], fake_info
        ), ["ALTER TABLE fake_connected ALTER COLUMN the_field SET DEFAULT 'vvv';"])
        self.assertEqual(database_f.VarcharField("the_field", default='v1').check_default(
            db_info_dict['v1'], fake_info
        ), [])
        
        # Drop it incase it affects any other tests
        try:
            cursor.execute("DROP TABLE fake_connected")
        except Exception:
            pass
        
    def test_validate(self):
        self.test_targets.extend([
            database_f.DBField.validate,
            database_f.BooleanField.validate,
            database_f.DateField.validate,
            database_f.DoubleField.validate,
            database_f.IntegerField.validate,
            database_f.SerialField.validate,
            database_f.TimestampField.validate,
        ])
        
        self.assertEqual(database_f.BooleanField("").validate("true"), True)
        self.assertEqual(database_f.BooleanField("").validate("false"), False)
        
        self.assertEqual(database_f.DateField("").validate("20-10-2010"), datetime.date(2010, 10, 20))
        self.assertEqual(database_f.DateField("").validate("20/10/2020"), datetime.date(2020, 10, 20))
        
        self.assertEqual(database_f.DoubleField("").validate("2.5"), 2.5)
        self.assertEqual(database_f.DoubleField("").validate(2.3), 2.3)
        self.assertEqual(database_f.DoubleField("", array=True).validate("{1.5, 1.3}"), [1.5, 1.3])
        
        self.assertEqual(database_f.IntegerField("").validate("25"), 25)
        self.assertEqual(database_f.IntegerField("").validate(23), 23)
        self.assertEqual(database_f.IntegerField("", array=True).validate("{15, 13}"), [15, 13])
        
        self.assertEqual(database_f.SerialField("").validate("25"), 25)
        self.assertEqual(database_f.SerialField("").validate(23), 23)
        
        # Timestamps need to be able to accept a variety of values
        self.assertEqual(
            database_f.TimestampField("").validate(1335972097),
            datetime.datetime(2012, 5, 2, 16, 21, 37)
        )
        self.assertEqual(
            database_f.TimestampField("").validate(1335982051.485074),
            datetime.datetime(2012, 5, 2, 19, 7, 31, 485074)
        )
        self.assertEqual(
            database_f.TimestampField("").validate("20-10-2010"),
            datetime.datetime(2010, 10, 20)
        )
        self.assertEqual(
            database_f.TimestampField("").validate("20/10/2020 10:30:59"),
            datetime.datetime(2020, 10, 20, 10, 30, 59)
        )
    
    def test_dbfield_escape(self):
        self.test_targets.extend([
            database_f.DBField.escape,
            database_f.DateField.escape,
            database_f.TextField.escape,
            database_f.TimestampField.escape,
            database_f.VarcharField.escape,
        ])
        
        for str_in, expected in self.escape_vals:
            self.assertEqual(database_f.DateField("").escape(str_in), expected)
            self.assertEqual(database_f.TextField("").escape(str_in), expected)
            self.assertEqual(database_f.TimestampField("").escape(str_in), expected)
            self.assertEqual(database_f.VarcharField("").escape(str_in), expected)
    
    def test_create_column(self):
        self.test_targets.append(database_f.DBField.create_column)
        
        self.assertEqual(database_f.BooleanField("the_field").create_column(), "the_field boolean NOT NULL default 'False'")
        self.assertEqual(database_f.DateField("the_field").create_column(), "the_field date NOT NULL default '2000-01-01'")
        self.assertEqual(database_f.DoubleField("the_field").create_column(), "the_field double precision NOT NULL default '0'")
        self.assertEqual(database_f.IntegerField("the_field").create_column(), "the_field integer NOT NULL default '0'")
        self.assertEqual(database_f.SerialField("the_field").create_column(), "the_field Serial NOT NULL")
        self.assertEqual(database_f.TextField("the_field").create_column(), "the_field text NOT NULL default ''")
        self.assertEqual(database_f.TimestampField("the_field").create_column(), "the_field timestamp without time zone NOT NULL default '2000-01-01 00:00:00'")
        self.assertEqual(database_f.VarcharField("the_field").create_column(), "the_field varchar(255) NOT NULL default ''")
    
    
    