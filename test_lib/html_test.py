import unittest
from http import cookies
from profiteer import html_f
import itertools

class ConfigTester(unittest.TestCase):
    test_targets = []
    
    maxDiff = None
    
    def test_js_name(self):
        self.test_targets.append(html_f.js_name)
        
        vals = (
            ("abc", "abc"),
            ("abc'd", "abc\\'d"),
            ("('my_name')", "\\'my_name\\'"),
        )
        
        for str_in, expected in vals:
            self.assertEqual(html_f.js_name(str_in), expected)
    
    def test_HTTP404(self):
        self.test_targets.append(html_f.HTTP404.main)
        
        vals = (
            ([], {"mode":"list_players"}, "<br /><div class='error'>404 for list_players</div>"),
        )
        
        for args, kwargs, expected in vals:
            mode = kwargs.get("mode", "")
            self.assertEqual(html_f.HTTP404(mode).main(*args, **kwargs), expected)
    
    def test_cookies(self):
        self.test_targets.append(html_f.set_cookie)
        self.test_targets.append(html_f.delete_cookie)
        self.test_targets.append(html_f.get_cookie)
        
        # Wipe the cookies to start with
        html_f.cookies = cookies.SimpleCookie()
        
        self.assertEqual(html_f.get_cookie("nonexistant_cookie"), None)
        
        # Lets try setting one
        html_f.set_cookie("imaginary_cookie", "math.sqrt(-1)")
        self.assertEqual(html_f.get_cookie("imaginary_cookie"), "math.sqrt(-1)")
        
        # Delete
        html_f.delete_cookie("imaginary_cookie")
        self.assertEqual(html_f.get_cookie("nonexistant_cookie"), None)
    
    def test_sort(self):
        self.test_targets.append(html_f._sort_elements)
        
        vals = (
            ([2,3,1], [1,2,3]),
            (set(["c","a","b"]), ["a","b","c"]),
        )
        
        for sequence, expected in vals:
            result = html_f._sort_elements(sequence)
            ordered_result = [v for k,v in result.items()]
            
            self.assertEqual(ordered_result, expected)
    
    def test_form_elements(self):
        """There won't be a lot gained from testing the actual output of these
        functions so what we're going to do is ensure we get _some_ output
        and that we don't cause an exception"""
        
        self.test_targets.extend([
            html_f.check_box,
            html_f.doubleclick_text,
            html_f.doubleclick_text_full,
            html_f.live_option_box,
            html_f.option_box,
            html_f.text_box,
            html_f.textarea,
        ])
        
        # check_box(name, checked=False, custom_id=''):
        vals = itertools.product(
            ["name1", "name2"],
            [True, False],
            ["", "custom_id"],
        )
        
        for args in vals:
            self.assertNotEqual(html_f.check_box(*args), "")
        
        # doubleclick_text(table, field, where_id, value, label_style="", size=10):
        vals = itertools.product(
            ["table1", ""],
            ["field1", ""],
            [0, 1, 2],
            ["value1", 5],
            ["", "font-weight:bold;"],
            [0, 5, 10],
        )
        
        for args in vals:
            self.assertNotEqual(html_f.doubleclick_text(*args), "")
        
        # doubleclick_text_full(table, field, where_field, value, label_style="", size=10):
        vals = itertools.product(
            ["table1", ""],
            ["field1", ""],
            ["id=5", "name='x'"],
            [0, 1, "X"],
            ["", "font-weight:bold;"],
            [0, 5, 10],
        )
        
        for args in vals:
            self.assertNotEqual(html_f.doubleclick_text_full(*args), "")
        
        # live_option_box(elements, table, field, where_id, value, tab_index = -1, style="", disabled=[], element_property="name", sort=True):
        vals = itertools.product(
            [{"1":"a","2":"b","3":"c"}],
            ["table1", ""],
            ["field1", ""],
            [0, 1, 2],
            ["value1", 5],
            [-1, 10, 1000000],
            ["", "font-weight:bold;"],
            [[1,2,3], []],
            ["name", "property-name"],
            [True, False],
        )
        
        for args in vals:
            self.assertNotEqual(html_f.live_option_box(*args), "")
        
        # option_box(name, elements, selected="", tab_index = -1, custom_id="<>", onchange="", style="", disabled=[], insert_dud=False, element_property="name", sort=True):
        vals = itertools.product(
            ["name1", ""],
            [{"1":"a","2":"b","3":"c"}],
            ["selected", ""],
            [-1, 10, 1000000],
            ["custom_id", "<>", ""],
            ["onchange", ""],
            ["style", ""],
            [[1,2,3], []],
            ["Insert dud", False],
            ["", "element property"],
            [True, False],
        )
        
        for args in vals:
            self.assertNotEqual(html_f.option_box(*args), "")
        
        # text_box(name, text='', size=15, tabIndex=-1, onchange='', custom_id='<>', style="", warn_on=None, disabled=False):
        vals = itertools.product(
            ["name1", ""],
            ["", "some text"],
            [0, 1, 15, 2000],
            [-1, 10, 1000000],
            ["onchange", ""],
            ["custom_id", "<>", ""],
            ["style", ""],
            [None],# Needs to be a function or none
            [True, False],
        )
        
        for args in vals:
            self.assertNotEqual(html_f.text_box(*args), "")
        
        # textarea(name, text='', rows=6, cols=30, tabIndex=-1, onchange='', custom_id='<>', style="", warn_on=None):
        vals = itertools.product(
            ["name1", ""],
            ["", "some text"],
            [0, 6, 100],
            [0, 30, 1000],
            [-1, 30, 1000],
            ["onchange", ""],
            ["custom_id", "<>", ""],
            ["style", ""],
            [None],# Needs to be a function or none
        )
        
        for args in vals:
            self.assertNotEqual(html_f.textarea(*args), "")
