import unittest
from profiteer.gui import get_one_field, edit_one_field
from profiteer.test_lib import gui_test_utils
from profiteer import database_f

class HTTPTester (unittest.TestCase):
    test_targets = [
        get_one_field.main,
        edit_one_field.main,
    ]
    
    maxDiff = None
    
    def test_one_field(self):
        cursor = database_f.get_cursor()
        
        # Test string field
        gui_test_utils.new_cgi_form((
            ("table",   "users"),
            ("field",   "username"),
            ("where",   "id = 1"),
            ("p",       False),
        ))
        
        self.assertEqual("admin", get_one_field.main(cursor))
        
        # Test boolean field
        gui_test_utils.new_cgi_form((
            ("table",   "users"),
            ("field",   "root"),
            ("where",   "id = 1"),
            ("p",       False),
        ))
        
        self.assertEqual(True, get_one_field.main(cursor))
        
        # Now test setting it
        gui_test_utils.new_cgi_form((
            ("table",   "users"),
            ("field",   "root"),
            ("where",   "id = 1"),
            ("value",   "False"),
            ("p",       False),
        ))
        
        self.assertEqual('False', edit_one_field.main(cursor))
        
        # Get it again
        gui_test_utils.new_cgi_form((
            ("table",   "users"),
            ("field",   "root"),
            ("where",   "id = 1"),
            ("p",       False),
        ))
        
        self.assertEqual(False, get_one_field.main(cursor))
