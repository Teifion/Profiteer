#!/usr/bin/env python3

from profiteer import common_f

common_f.cache['test_mode'] = True

from profiteer import database_f, config
from profiteer import sync as sync_module

# Set to test database, just incase something tries to get a new cursor
database_f.dbname   = config.get("test_db_name")

import sys
import unittest

# Data to setup the test database
dummy_data = """INSERT INTO errors ("timestamp", "args", "user_id", "mode", "exception_type", "traceback")
    values
('2010-01-01 20:20:20', 'a=1', 1, 'list_users', 'Exception', 'traceback'),
('2010-01-02 20:20:20', 'a=2', 1, 'list_users', 'Exception', 'traceback'),
('2010-01-03 20:20:20', 'a=3', 1, 'list_users', 'Exception', 'traceback'),
('2010-01-03 20:20:20', 'a=4', 1, 'list_users', 'Exception', 'traceback'),
('2010-01-03 20:20:20', 'a=5', 1, 'list_users', 'Exception', 'traceback');
"""

def setup_test_db():
    cursor = database_f.get_test_cursor()
    
    # Strip it down
    tables = []
    query = """SELECT tablename FROM pg_tables WHERE schemaname = 'public'"""
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    for row in cursor:
        tables.append(row['tablename'])
    
    for t in tables:
        query = """DROP TABLE {} CASCADE""".format(t)
        try: cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    query = """SELECT tablename FROM pg_tables WHERE schemaname = 'public'"""
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    for row in cursor:
        raise Exception("Not all tables deleted, found table %s" % row['tablename'])
    
    # Build structure
    sync_module.main(fix=True, print_output=False)
    
    # Populate it with the test data
    path = "{}/test_lib/test_setup.sql".format(sys.path[0])
    with open(path) as f:
        query = dummy_data + f.read()
    
    if query != "":
        try:
            cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    # Test to ensure we list the right number of tables
    tables = 0
    query = """SELECT tablename FROM pg_tables WHERE schemaname = 'public'"""
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    for row in cursor:
        tables += 1
    
    if tables != len(sync_module.table_list):
        raise Exception("Error: Tables listed ({}) does not match the length of sync.table_list: {}".format(tables, len(sync_module.table_list)))
