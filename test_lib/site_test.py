import unittest
from profiteer import database_f, web, user
from profiteer.test_lib import gui_test_utils
import data

# We need to import this to load the non-framework pages for testing
import web as root_web

# Pages we don't want to try, it might be they call
# external resources or something
skip_pages = ["emulate_user"] + data.skip_pages

# Pages we expect an exception from
expect_exception = [
    "edit_one_field",
    "get_one_field",
    "lookup",
    "edit_error",
    # "emulate_user"
] + data.expect_exception

class Web_class (unittest.TestCase):
    test_targets = [
        web.import_page,
        web.de_unicode,
        web._print_ignoring_error,
        
        # If this doesn't work you're going to find out real fast
        web.main,
    ]
    
    def test_print_ignoring_error(self):
        vals = (
            # No change
            ("XYZ", "XYZ"),
            
            # Changed
            ("á", "<strong style='color:#F00;'>*</strong>")
        )
        
        for text_in, expected in vals:
            self.assertEqual(web._print_ignoring_error(text_in, test_mode=True), expected)
    
    def test_webpy_page(self):
        cursor = database_f.get_cursor()
        
        origional_require = user.require
        user.require = emulate_require
        
        for page_name in web.page_dict.keys():
            if page_name in skip_pages: continue
            
            # Reset the CGI form each time so we're not sending data
            gui_test_utils.new_cgi_form({})
            
            the_page = web.import_page(page_name, handle_exception=False)
            
            if page_name in expect_exception:
                try:
                    self.assertRaises(Exception, the_page.main, cursor)
                except Exception:
                    print("")
                    print("Page name: %s" % page_name)
                    raise
                
            else:
                try:
                    the_page.main(cursor)
                except Exception:
                    print("")
                    print(page_name)
                    raise
            
        user.require = origional_require
        
    def test_de_unicode(self):
        vals = (
            ("abcde", "abcde"),
            ("-=_-=:)()", "-=_-=:)()"),
            ("'¡", "'¡"),
            ("’‘“”", "&rsquo;&lsquo;&ldquo;&rdquo;"),
        )
        
        for str_in, expected in vals:
            self.assertEqual(expected, web.de_unicode(str_in))

def emulate_require(*privileges):
    def wrap(f):
        def _func(cursor, *args, **kwargs):
            return f(cursor, *args, **kwargs)
            
        return _func
    return wrap
