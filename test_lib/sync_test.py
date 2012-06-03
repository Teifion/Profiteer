import unittest
from profiteer.test_lib import database_test
from profiteer import database_f, sync_f, sync_q

FakeConnected = database_test.FakeConnected
fake_info = database_test.FakeConnected.table_info

class SyncTester (unittest.TestCase):
    test_targets = []
    
    maxDiff = None
    
    def test_check_structure(self):
        self.test_targets.append(sync_f.check_table)
        self.test_targets.append(sync_f.check_table_fields)
        self.test_targets.append(sync_f.create_table)
        
        cursor = database_f.get_test_cursor()
        
        # Just incase it's lingering from a previous test
        try:
            cursor.execute("DROP TABLE fake_connected")
        except Exception:
            pass
        
        r = sync_f.check_table(cursor, fake_info, fix=False, show_fixes=True, die_queitly=False)
        
        self.assertEqual(r, """create table fake_connected
(
s1 Serial NOT NULL,
v1 varchar(255) NOT NULL default 'v1',
v2 varchar(255) NOT NULL default 'v2',
i1 integer NOT NULL default '1',
i2 integer NOT NULL default '2',
t1 text NOT NULL default 't1',
t2 text NOT NULL default 't2',
d1 double precision NOT NULL default '1.1',
b1 boolean NOT NULL default 'True',
afield integer[] NOT NULL default '{0}',
bfield integer[] NOT NULL default '{1,2}',
date_field date NOT NULL default '2000-10-30',
time_field timestamp without time zone NOT NULL default '2000-10-30 12:50:59',
primary key (s1)
)
\033[31mTable missing\033[30;0m (fake_connected)""")
        
        # Now we actually fix it
        sync_f.check_table(cursor, fake_info, fix=True, show_fixes=False, die_queitly=False)
        
        # And make sure it's done properly
        r = sync_f.check_table(cursor, fake_info, fix=False, show_fixes=True, die_queitly=False)
        self.assertEqual("\033[32mfake_connected is correct\033[30;0m", r)
        
        #   TEST CHECK_TABLE_FIELDS
        #------------------------
        # Start by making sure it shows as correct
        r = sync_f.check_table_fields(cursor, fake_info, fix=False, show_fixes=False)
        self.assertEqual("\033[32mfake_connected is correct\033[30;0m", r)
        
        # Drop a field from the table to make sure we'll fix it
        query = """ALTER TABLE fake_connected DROP COLUMN t1;"""
        try: cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
        
        r = sync_f.check_table_fields(cursor, fake_info, fix=False, show_fixes=True)
        self.assertEqual("""\033[31mcolumn missing in fake_connected\033[30;0m (t1)
  Fixes:
alter table fake_connected add column t1 text NOT NULL default 't1'
""", r)
        
        # Drop the table, just to make sure it doesn't mess with anything else
        query = """DROP TABLE fake_connected"""
        try: cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    def test_create_table(self):
        pass
    
    def test_check_table(self):
        pass
    
    def test_create_field(self):
        pass
