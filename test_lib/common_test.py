import unittest
from profiteer import common_f, common_q, error, database_f
import datetime
from profiteer.test_lib import gui_test_utils

class CommonTester(unittest.TestCase):
    test_targets = []
    
    maxDiff = None
    
    def test_approx(self):
        self.test_targets.append(common_f.approx)
        vals = (
            (1001, 1000),
        )
        
        for number_in, expected in vals:
            result = common_f.approx(number_in)
            
            self.assertEqual(result, expected)
          
    def test_convert_date(self):
        self.test_targets.append(common_f.convert_date)
        this_year = datetime.date.today().year
        
        vals = (
            # Two sections
            ("01-02", datetime.date(this_year, 2, 1)),
            ("01/03", datetime.date(this_year, 3, 1)),
            ("01 04", datetime.date(this_year, 4, 1)),
            
            ("11-12", datetime.date(this_year, 12, 11)),
            ("21/10", datetime.date(this_year, 10, 21)),
            ("30 11", datetime.date(this_year, 11, 30)),
            
            # Three sections
            ("01-02-10", datetime.date(2010, 2, 1)),
            ("01/03-11", datetime.date(2011, 3, 1)),
            ("01 04-12", datetime.date(2012, 4, 1)),
            
            ("11-12-2010", datetime.date(2010, 12, 11)),
            ("21/10-2011", datetime.date(2011, 10, 21)),
            ("30 11-2012", datetime.date(2012, 11, 30)),
        )
        
        for str_in, expected in vals:
            answer = common_f.convert_date(str_in)
            self.assertEqual(answer, expected)
        
    def test_display_array(self):
        self.test_targets.append(common_f.display_array)
        vals = (
            # No values
            ([], "[]"),
            
            # 1 values
            ([1], "1"),
            (["1"], "1"),
            
            # 3 values
            ([1,2,3], "1, 2,&nbsp;&nbsp; +1 more"),
            
            # 100 values
            ([1]*100, "1, 1,&nbsp;&nbsp; +98 more")
        )
        
        for val_in, expected in vals:
            self.assertEqual(common_f.display_array(val_in), expected)
        
        # Now test with lookup
        self.assertEqual(common_f.display_array(
            array = ["a", "b"],
            dictionary = {"a":1,"b":2}
        ), "1, 2")
        
        # Max names
        self.assertEqual(common_f.display_array([1]*100, max_names=5), "1, 1, 1, 1, 1,&nbsp;&nbsp; +95 more")
    
    def test_display_date(self):
        self.test_targets.append(common_f.display_date)
        self.test_targets.append(common_f.th_of_month)
        
        vals = (
            ("%d of %B", datetime.date(2012, 1, 1), "01st of January"),
            ("%d of %B", datetime.date(2012, 3, 2), "02nd of March"),
            ("%d of %B", datetime.date(2012, 6, 3), "03rd of June"),
            ("%d of %B", datetime.date(2012, 10, 4), "04th of October"),
            
            ("%d of %B", datetime.date(2012, 1, 11), "11th of January"),
            ("%d of %B", datetime.date(2012, 3, 12), "12th of March"),
            ("%d of %B", datetime.date(2012, 6, 13), "13th of June"),
            
            ("%d of %B", datetime.date(2012, 1, 21), "21st of January"),
            ("%d of %B", datetime.date(2012, 3, 22), "22nd of March"),
            ("%d of %B", datetime.date(2012, 6, 23), "23rd of June"),
            ("%d of %B", datetime.date(2012, 10, 24), "24th of October"),

        )
        
        for format_string, the_date, expected in vals:
            self.assertEqual(common_f.display_date(the_date, format_string), expected)
    
    def test_cgi_form_functions(self):
        self.test_targets.append(common_f.get_val)
        self.test_targets.append(common_f.print_post_data)
        
        gui_test_utils.new_cgi_form((
            ("a",   1),
            ("b",   2),
            ("c",   3),
        ))
        
        self.assertEqual(common_f.get_val("a"), 1)
        self.assertEqual(common_f.get_val("b"), 2)
        self.assertEqual(common_f.get_val("c"), 3)
        
        self.assertEqual(common_f.print_post_data(joiner="\n"), """a = 1
b = 2
c = 3""")
        
    def ttest_queries(self):
        cursor = database_f.get_test_cursor()
        
        self.test_targets.extend([common_q._make_query, common_q.id_list, common_q.get_one,
            common_q.get_all, common_q.get_where, common_q.get_last])
        
        # ID List
        self.assertEqual(common_q.id_list(cursor, error.Error), [1,2,3,4,5])
        
        # All
        self.assertEqual(len(common_q.get_all(cursor, error.Error)), 5)
        self.assertEqual(type(common_q.get_all(cursor, error.Error, where="id=1")[1]), error.Error)
        self.assertEqual(len(common_q.get_all(cursor, error.Error, where="id>3")), 2)
        
        # One
        result = common_q.get_one(cursor, error.Error, id=1)
        fake = error.Error({
            "id":               1,
            "timestamp":        1000,
            "args":             "a=1",
            "mode":             "list_users",
            "user_id":          1,
            "exception_type":   "Exception",
            "traceback":        "traceback",
        })
        
        if result != fake:
            print(result.compare(fake))
            self.assertEqual(result, fake)
        
        # Where
        self.assertEqual(
            common_q.get_all(cursor, error.Error, where='"timestamp" = 3000'),
            common_q.get_where(cursor, error.Error, timestamp=3000)
        )
        
        # Last
        self.assertEqual(
            common_q.get_all(cursor, error.Error, where='id = 5')[5],
            common_q.get_last(cursor, error.Error)
        )
