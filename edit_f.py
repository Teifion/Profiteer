"""
A set of functions for performing updates to the database from HTML forms.
"""

from profiteer import common_q, common_f

def add(cursor, class_type):
    the_obj = class_type()
    the_obj.get_from_form(cursor, common_f.cgi_form.list)
    
    the_obj.insert(cursor)
    
    return the_obj

def commit(cursor, class_type):
    the_obj = class_type()
    the_obj.get_from_form(cursor, common_f.cgi_form.list)
    
    the_obj.update(cursor)
    
    return the_obj

def delete(cursor, class_type, **wheres):
    the_obj = common_q.get_one(cursor, class_type, **wheres)
    the_obj.delete(cursor)
    
    return the_obj

def custom_func(cursor, class_type, func_name, **wheres):
    the_obj = common_q.get_one(cursor, class_type, **wheres)
    getattr(the_obj, func_name)(cursor)
    
    return the_obj
