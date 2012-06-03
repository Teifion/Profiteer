from profiteer import user_log, common_q, config, common_f, html_f, database_f, error
from hashlib import md5
import os
import random
import string
import data

class User (database_f.DBConnectedObject):
    table_info = {
        "Name":         "users",
        "Indexes":      {
            "username": "username",
        },
        "Fields":       [
            database_f.SerialField("id",                primary_key=True),
            database_f.VarcharField("username",         max_length=40),
            database_f.VarcharField("password",         max_length=32),
            
            database_f.BooleanField("root",             default=False),
            
            database_f.VarcharField("salt",             max_length=32),
            database_f.BooleanField("blocked",          default=False),
        ] + data.user_fields,
        "Data": ("""INSERT INTO users (username, password, salt, root)
                values
                ('admin', '', 'K*WJgU&j8M) ZT?=J_T-TUfH9*lY#!>@', True);""",
        ),
    }
    
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
    
    def has_privileges(self, *privileges):
        missing = []
        
        for p in privileges:
            if not getattr(self, p):
                missing.append(p)
        
        return missing
    
    def get_from_form(self, cursor, form_list):
        super(User, self).get_from_form(cursor, form_list)
        
        # If they send a password then we want to make sure they confirm it
        if hasattr(self, "password"):
            for http_data in form_list:
                if http_data.name == "password2":
                    if self.password != http_data.value:
                        del(self.password)
        
        # If it is a new password
        if hasattr(self, "password") and self.password != None:
            self.password = encode_password(self.password, self.salt)
        
permission_fields = []

for f in User.table_info['Fields']:
    if f.field_type == "boolean":
        if f.name == "blocked": continue
        
        permission_fields.append(f.name)

# This generates a list of characters we can use in a salt
# based on string.printable minus a few unwanted occupants
saltable = [c for c in string.printable if c not in ("\x0b", "\x0c", "\n", "\t", "\r", "\\")]

def make_salt():
    return "".join([random.choice(saltable) for x in range(32)])

def get_user(cursor, username, password, from_cookie=False):
    u = None
    
    query = """SELECT * FROM users WHERE lower(username) = '{}'""".format(database_f.escape(username))
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    for row in cursor:
        u = User(**row)
    
    if u == None:
        return "Username not found"
    
    # Do we need to hash the password?
    h_password = password
    if not from_cookie:
        h_password = encode_password(password, u.salt, passes=1)
    
    # Is the password correct?
    if h_password != u.password:
        return "Incorrect password"
    
    # It's correct, return the user instance
    common_f.cache['user'] = u
    return u

def encode_password(password, salt, passes=1):
    if passes > 1:
        password = encode_password(password, salt, passes-1)
    
    passcode = config.get("passcode")
    
    m = md5()
    m.update(passcode.encode("utf-8"))
    m.update(password.encode("utf-8"))
    m.update(salt.encode("utf-8"))
    return m.hexdigest()

def attempt_login(cursor):
    username, password = "", ""
    
    # Try to get it from CGI, failing that try cookies
    # Don't try to get it from CGI if it's mode=edit_user
    if common_f.get_val('mode',"") != "edit_user":
        username = common_f.get_val('username', "")
        password = common_f.get_val('password', "")
        from_cookie = False
    
    # Cookies method
    if username == "" and password == "":
        username = html_f.get_cookie('profiteer_username', "")
        password = html_f.get_cookie('profiteer_password', "")
        from_cookie = True
    
    # Still nothing?
    if username == "" and password == "":
        if os.environ.get('REMOTE_ADDR') == "::1" or os.environ.get('REMOTE_ADDR') == None:
            u = common_q.get_one(cursor, User, id=1)
            common_f.cache['user'] = u
            return u
        return ""
    
    response = get_user(cursor, username, password, from_cookie)
    
    if type(response) == User:
        html_f.set_cookie("profiteer_username", username)
        html_f.set_cookie("profiteer_password", response.password)
    
    return response

def logout(cursor):
    html_f.set_cookie("profiteer_username", "")
    html_f.set_cookie("profiteer_password", "")

# Prints out the login form
def login_form(message, username=""):
    if message == "Incorrect password" and username == "":
        username = common_f.get_val('username', "")
    
    return """
    <form action="web.py?mode=login" method="post" accept-charset="utf-8" style="text-align:center;">
        <br />
        {message}
        <br />
        <br /><br />

        <div style="border:1px solid #AAA; width:250px; margin: 0 auto;">
            <table border="0" cellspacing="5" cellpadding="5" style="margin: 0 auto;">
                <tr>
                    <td><label for="username">Username:</label></td>
                    <td><input type="text" name="username" id="username" value="{username}" /></td>
                </tr>
                <tr>
                    <td><label for="password">Password:</label></td>
                    <td><input type="password" name="password" id="password" value="" /></td>
                </tr>
                <tr>
                    <td colspan="2">
                        <input type="submit" value="Login" />
                    </td>
                </tr>
            </table>
        </div>
    </form>
    {onload}""".format(
        onload = html_f.onload % "$('#username').focus();",
        message = '<div class="error">%s</div>' % message if message != "" else "",
        username = username,
    )

def no_access(message="You do not have access to this section", missing=[]):
    return """
    <br /><br />
    <div class="error">
        {message}
    </div>
    <br><br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    {missing}""".format(
        message = message,
        missing = "Missing: " + ", ".join(missing) if missing != [] else "",
    )

# Useful article on decorators with arguments
# http://www.artima.com/weblogs/viewpost.jsp?thread=240845
def require(*privileges):
    def wrap(f):
        def _func(cursor, *args, **kwargs):
            response = attempt_login(cursor)
            
            # If it's a string they've failed to login
            if type(response) == str:
                return login_form(response)
            
            # They are logged in, now we need to make sure they have the privilages
            if response.has_privileges(*privileges) != []:
                if response.root:
                    return no_access(missing=response.has_privileges(*privileges))
                return no_access()
            
            # Try to get the page itself
            try:
                page_result = f(cursor, *args, **kwargs)
            except Exception as e:
                if common_f.cache['user'].root or False:
                    print(error.html_render())
                    exit()
                else:
                    return error.log_error(cursor, e, context=0)
            
            # Try logging the usage, if not we'll quietly log the error
            try:
                if config.get("log_usage") and common_f.get_val("ajax", False) == False:
                    user_log.log_usage(cursor)
            except Exception as e:
                error.log_error(cursor, e)
            
            return page_result
            
        return _func
        
        _func.__name__ = f.__name__
        _func.__doc__ = f.__doc__
    
    return wrap
