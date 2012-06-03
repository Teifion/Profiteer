import re
import cgi
import datetime

cgi_form = cgi.FieldStorage()

# Used to store values that will be used for the duration of this script
# and also for saving commonly pulled values from the database
cache = {
    'mode':         '',
    'test_mode':    False,
    "user":         None,
    
    "date_DM":      re.compile(r'^([0-9]{1,2})[ /\-]([0-9]{1,2})$'),
    "date_DMY":     re.compile(r'^([0-9]{1,2})[ /\-]([0-9]{1,2})[ /\-]([0-9]{1,4})$'),
    "date_time":    re.compile(r'^([0-9]{1,2})[ /\-]([0-9]{1,2})[ /\-]([0-9]{1,4}) ([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})$'),
}

def approx(n):
    """Gives an approximate value"""
    if n < 10:          return 10
    if n < 50:          return 50
    if n < 100:         return 100
    if n < 500:         return 500
    if n < 1000:        return 1000
    if n < 10000:       return int(round(n, -3))
    if n < 100000:      return int(round(n, -4))
    if n < 1000000:     return int(round(n, -4))
    if n < 10000000:    return int(round(n, -5))
    if n < 100000000:   return int(round(n, -6))
    
    raise Exception("Number too big")

def convert_date(str_date):
    """Takes a date from a user (in D-M-Y format) and converts it into a Python date
    can also handle timestamps (D-M-Y H:M:S)"""
    
    str_date = str_date.strip()
    if str_date == "":
        return None
    
    # Three sections
    result = cache['date_DMY'].search(str_date)
    if result != None:
        d = int(result.groups()[0])
        m = int(result.groups()[1])
        y = int(result.groups()[2])
        if y < 1000: y += 2000
        return datetime.date(y,m,d)
    
    # Two sections
    result = cache['date_DM'].search(str_date)
    if result != None:
        d = int(result.groups()[0])
        m = int(result.groups()[1])
        y = datetime.date.today().year
        return datetime.date(y,m,d)
    
    # Timestamp?
    result = cache['date_time'].search(str_date)
    if result != None:
        d = int(result.groups()[0])
        m = int(result.groups()[1])
        y = int(result.groups()[2])
        
        h = int(result.groups()[3])
        mm = int(result.groups()[4])
        s = int(result.groups()[5])
        
        if y < 1000: y += 2000
        
        return datetime.datetime(y, m, d, h, mm, s)
    
    else:
        raise Exception("Unable to match string input of '%s'" % str_date)

def get_val(value_name, default = ''):
    """Get value from post/get data"""
    for http_data in cgi_form.list:
        if http_data.name == value_name:
            return http_data.value
    
    return default

# Useful for debugging stuff
def print_post_data(joiner="<br />"):
    """Print out the information from the web-form"""
    output = []
    
    for http_data in cgi_form.list:
        output.append("%s = %s" % (http_data.name, http_data.value))
        
    return joiner.join(output)

def display_array(array, dictionary={}, property_name="name", max_names=2):
    def _get(k):
        if k not in dictionary and dictionary != {}:
            return '<span class="error">!%s</span>' % k
        
        if dictionary == {}:
            v = k
        else:
            v = dictionary[k]
        
        if type(v) in (str, int, float):
            return str(v)
        else:
            return getattr(v, property_name)
    
    if len(array) == 0:
        return "[]"
    
    if len(array) == 1:
        return "%s" % _get(array[0])
    
    if len(array) <= max_names:
        return "%s" % (", ".join([str(_get(k)) for k in array]))
    
    if len(array) > max_names:
        return "%s,&nbsp;&nbsp; +%d more" % (", ".join([str(_get(k)) for k in array[0:max_names]]), len(array) - max_names)

# Appends "st, nd, rd, th" to the relevant days of the month
def display_date(the_date, format_string="%d of %B"):
    day = the_date.day
    format_string = format_string.replace("%d", "%d{}".format(th_of_month(day)))
    return the_date.strftime(format_string)

def th_of_month(day):
    if int(day) in (1, 21, 31): return "st"
    if int(day) in (2, 22, 32): return "nd"
    if int(day) in (3, 23, 33): return "rd"
    return "th"
