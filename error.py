import inspect
import linecache
import os
import pydoc
import sys
import time
import traceback
import cgitb
import datetime

import cgi
from profiteer import common_f, database_f
from profiteer.gui import pages

# http://www.codinghorror.com/blog/2009/04/exception-driven-development.html
class Error (database_f.DBConnectedObject):
    table_info = {
        "Name":         "errors",
        "Indexes":      {
        },
        "Fields":       (
            database_f.SerialField("id",            primary_key=True),
            
            database_f.TimestampField("timestamp"),
            database_f.TextField("args"),
            
            database_f.IntegerField("user_id"),
            database_f.VarcharField("mode"),
            database_f.VarcharField("function_call"),
            database_f.VarcharField("exception_type"),
            
            database_f.BooleanField("fixed", default=False),
            
            database_f.TextField("traceback"),
        ),
    }
    
    def __init__(self, *args, **kwargs):
        if "timestamp" not in kwargs:
            kwargs['timestamp'] = int(time.time())
        
        super(Error, self).__init__(*args, **kwargs)

styles = {
    "body":             "background-color:#FFF;font-family:'helvetica', 'arial';",
    "header":           "background-color:#DFC;color:#000;padding:15px;",
    "frame":            "font-family:monospace;padding:10px;border-top:1px solid #AAA;background-color:#EEE;",
    "highlighted_row":  "background-color: #BBB;",
    "grey_text":        "color:#777;",
}

def log_error(cursor, e, context=5, function_call=""):
    error_output = html_render(sys.exc_info(), context=5, headers=False)
    
    # It might be they're not logged in
    if "user" in common_f.cache and common_f.cache['user'] != None:
        user_id = common_f.cache['user'].id
    else:
        user_id = -1
    
    exception_type = str(sys.exc_info()[0]).replace("<class '", "").replace("'>", "")
    
    # We log the error here
    the_error = Error(
        args           = common_f.print_post_data(joiner="\n\n"),
        user_id        = user_id,
        mode           = common_f.get_val("mode", pages.default_page),
        function_call = function_call,
        exception_type = exception_type,
        traceback      = error_output,
    )
    
    error_logged = True
    try:
        the_error.insert(cursor)
    except Exception as e:
        if context != 0:
            raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), the_error.insert(test_mode=True)))
        else:
            error_logged = False
    
    # Display an output here
    if context == 0:
        # No context means it's a user we don't want seeing the stack trace
        
        cgi_form = cgi.FieldStorage()
        
        return """<br><div class="error">
            There has been an error. {error_logged}
        </div>
        
        <div style="padding:10px">
            Below is a copy of all the data you submitted.
            <br>
            <hr>
            <br>
            
            {cgi_form}
        </div>
        """.format(
            cgi_form = "<br><br>".join([str(http_data.value) for http_data in cgi_form.list]),
            error_logged = "The error has been logged automatically." if error_logged else "The error could not be logged"
        )
    
    # No limit to context, this means we can print the stack trace
    return ("Content-type: text/html; charset=utf-8" + "\n" + error_output)

def html_render(einfo=None, context=5, headers=True):
    """Copied from cgitb.html() and altered to suit my needs and preferences"""
    
    # If no info passed, grab it from the sys library
    if einfo == None:
        einfo = sys.exc_info()
    
    etype, evalue, etb = einfo
    if isinstance(etype, type):
        etype = etype.__name__
    
    indent = str(('&nbsp;' * 6))
    frames = []
    records = inspect.getinnerframes(etb, context)
    
    final_file, final_line = "", 0
    
    for frame, the_file, lnum, func, lines, index in records:
        if the_file:
            file_path = os.path.abspath(the_file)
            final_file = file_path
            link = '<a href="file://{}">{}</a>'.format(file_path, pydoc.html.escape(file_path))
        else:
            the_file = link = '?'
        
        args, varargs, varkw, locals = inspect.getargvalues(frame)
        call = ''
        if func != '?':
            call = 'in <strong>' + func + '</strong>' + \
                inspect.formatargvalues(args, varargs, varkw, locals,
                    formatvalue=lambda value: '=' + pydoc.html.repr(value))
        
        highlight = {}
        
        def reader(lnum=[lnum]):
            highlight[lnum[0]] = 1
            try: return linecache.getline(the_file, lnum[0])
            finally: lnum[0] += 1
        vars = cgitb.scanvars(reader, frame, locals)
        
        rows = []
        if index is not None:
            i = lnum - index
            for line in lines:
                num = "<span style='font-size:0.8em;'>" + '&nbsp;' * (5-len(str(i))) + str(i) + '</span>&nbsp;'
                if i in highlight:
                    final_line = i
                    line = '=&gt;%s%s' % (num, pydoc.html.preformat(line))
                    rows.append('<div style="{}">{}</div>'.format(styles['highlighted_row'], line))
                else:
                    line = '&nbsp;&nbsp;%s%s' % (num, pydoc.html.preformat(line))
                    rows.append('<div style="%s">%s</div>' % (styles['grey_text'], line))
                i += 1

        done, dump = {}, []
        for name, where, value in vars:
            if name in done: continue
            done[name] = 1
            if value is not cgitb.__UNDEF__:
                if where in ('global', 'builtin'):
                    name = ('<em>%s</em> ' % where) + "<strong>%s</strong>" % name
                elif where == 'local':
                    name = "<strong>%s</strong>" % name
                else:
                    name = where + "<strong>" + name.split('.')[-1] + "</strong>"
                dump.append('%s&nbsp;= %s' % (name, pydoc.html.repr(value)))
            else:
                dump.append(name + ' <em>undefined</em>')

        rows.append('<div style="{};font-size:0.9em;">{}</div>'.format(styles['grey_text'], ', '.join(dump)))
        
        frames.append('''
        <div style="{styles[frame]}">
            {link} {call}
            {rows}
        </div>'''.format(
            styles = styles,
            link = link,
            call = call,
            rows = '\n'.join(rows)
        ))
        
        final_file, final_line
    
    exception = ['<br><strong>%s</strong>: %s' % (pydoc.html.escape(str(etype)),
                                pydoc.html.escape(str(evalue)))]
    for name in dir(evalue):
        if name[:1] == '_': continue
        value = pydoc.html.repr(getattr(evalue, name))
        exception.append('\n<br>%s%s&nbsp;=\n%s' % (indent, name, value))
    
    mode = common_f.get_val("mode", pages.default_page)
    if mode in pages.page_dict:
        path = "/".join(pages.page_dict[mode][1::-1])
    else:
        path = "NO PATH"
    
    output = """
    <html>
        <body style='padding:0;margin:0;'>
    
    <div id="exception_container" style="{styles[body]}">
        <div id="exception_header" style="{styles[header]}">
            <span style="font-size:2em;">{etype} at {short_file_path}.py</span><br />
            
            <div style="padding: 10px 30px;">
                <table border="0" cellspacing="0" cellpadding="5">
                    <tr>
                        <td style="text-align:right; width:200px;">Request url:</td>
                        <td>{url}.py</td>
                    </tr>
                    <tr>
                        <td style="text-align:right;">Exception type:</td>
                        <td>{etype}</td>
                    </tr>
                    <tr>
                        <td style="text-align:right;">Exception value:</td>
                        <td>{evalue}</td>
                    </tr>
                    <tr>
                        <td style="text-align:right;">Exception location:</td>
                        <td>{location}</td>
                    </tr>
                    <tr>
                        <td style="text-align:right;">Python executable:</td>
                        <td>{python_exe}</td>
                    </tr>
                    <tr>
                        <td style="text-align:right;">Python version:</td>
                        <td>{pyver}</td>
                    </tr>
                    <tr>
                        <td style="text-align:right;vertical-align: top;">Python path:</td>
                        <td>{pypath}</td>
                    </tr>
                    <tr>
                        <td style="text-align:right;">Server time:</td>
                        <td>{server_time}</td>
                    </tr>
                </table>
            </div>
        </div>
    
    </div>""".format(
        styles      = styles,
        
        url         = path,
        location    = final_file + ", line %d" % final_line,
        etype       = pydoc.html.escape(str(etype)),
        evalue      = pydoc.html.escape(str(evalue)),
        pyver       = sys.version.split()[0],
        python_exe  = sys.executable,
        pypath      = "<br>".join(sys.path),
        server_time = datetime.datetime.now().strftime("%A, %d of %b %Y %H:%M:%S %Z"),
        file_path   = path,
        
        # Takes file path and removes the root/system path from it
        short_file_path = path.replace(sys.path[0], ""),
    )
    
    if headers:
        output = "Content-type: text/html; charset=utf-8\n" + output
    
    # return output + ''.join(frames) + ''.join(exception) + '''
    return output + ''.join(frames) + '''


<!-- The above is a description of an error in a Python program, formatted
     for a Web browser because the 'cgitb' module was enabled.  In case you
     are not reading this in a Web browser, here is the original traceback:

%s
-->

</body>
</html>
''' % pydoc.html.escape(
          ''.join(traceback.format_exception(etype, evalue, etb)))

def emulate_require(*privileges):
    def wrap(f):
        def _func(cursor, *args, **kwargs):
            # They are logged in, now we need to make sure they have the privilages
            if common_f.cache['user'].has_privileges(*privileges) != []:
                missing = common_f.cache['user'].has_privileges(*privileges)
                
                return """
                <br /><br />
                <div class="error">
                    Insufficient priviliages
                </div>
                <br><br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                Missing: {missing}""".format(
                    missing = ", ".join(missing) if missing != [] else "",
                )
            
            return f(cursor, *args, **kwargs)
            
        return _func
    return wrap

def emulate_execute(execute_function):
    def f(query):
        if type(query) != str:
            print("")
            print("Query is not of type string: %s" % str(query))
            return
        
        # Allow SELECTS only
        if query[0:6].upper() == "SELECT":
            execute_function(query)
        
    return f
