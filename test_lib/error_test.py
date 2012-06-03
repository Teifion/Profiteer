import unittest
from profiteer.test_lib import database_test
from profiteer import user, error, database_f, common_f
from profiteer.test_lib import gui_test_utils

FakeConnected = database_test.FakeConnected
fake_info = database_test.FakeConnected.table_info

class ErrorTester (unittest.TestCase):
    test_targets = []
    
    maxDiff = None
    
    def test_emulate_require(self):
        self.test_targets.append(error.emulate_require)
        
        @error.emulate_require("noexistant_user_permission")
        def f(*args, **kwargs):
            return "X"
        
        self.assertEqual(f(1,2,3), "X")
    
    # This is used by gui/emulate_user.py
    def test_emulate_execute(self):
        self.test_targets.append(error.emulate_execute)
        
        # This allows us to monkey-patch the append function
        class MagicList(list): pass
        
        # In theory all queries to be appended will now go though this function
        queries = MagicList()
        queries.append = error.emulate_execute(queries.append)
        
        # SELECT is allowed
        queries.append("SELECT * FROM users")
        self.assertEqual(len(queries), 1)
        
        # INSERT is not allowed
        queries.append("INSERT INTO users (username) VALUES ('new_username');")
        self.assertEqual(len(queries), 1)
        
        # UPDATE is not allowed
        queries.append("UPDATE users SET username = 'new_username' WHERE id = 1;")
        self.assertEqual(len(queries), 1)
        
        # DELETE is most certainly now allowed
        queries.append("DELETE FROM users;")
        self.assertEqual(len(queries), 1)
    
    def test_html_render(self):
        self.test_targets.append(error.html_render)
        
        try:
            raise Exception("XYZ")
        except Exception:
            with_headers = error.html_render(einfo=None, context=5, headers=True)
            without_headers = error.html_render(einfo=None, context=5, headers=False)
        
        self.assertEqual(with_headers[0:39], "Content-type: text/html; charset=utf-8\n")
        self.assertNotIn("Content-type: text/html; charset=utf-8\n", without_headers)
    
    def test_log_error(self):
        self.test_targets.append(error.log_error)
        cursor = database_f.get_test_cursor()
        
        # First we make sure there is no error
        query = """DELETE FROM errors"""
        try: cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
        
        # We need to fake a user for the logging to work
        common_f.cache['user'] = user.User(id=1, username="username")
        
        # Fake args
        gui_test_utils.new_cgi_form((
            ("mode",   "list_users"),
            ("arg_1",   1),
            ("arg_3",   3),
        ))
        
        # Now we log the error
        try:
            raise Exception("This is an exception")
        except Exception as e:
            error.log_error(cursor, e, context=5)
        
        query = """SELECT * FROM errors"""
        try: cursor.execute(query)
        except Exception as e:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
            
        errors_found = []
        for row in cursor:
            errors_found.append(row)
        
        self.assertEqual(len(errors_found), 1)
        self.assertEqual(row['user_id'], 1)
        self.assertEqual(row['args'], "mode = list_users\n\narg_1 = 1\n\narg_3 = 3")
        self.assertEqual(row['exception_type'], "Exception")
        self.assertEqual(row['mode'], "list_users")
