import datetime
import time
from profiteer import error, user, common_q, common_f, html_f, database_f

page_data = {
    "Template": "admin",
    "Title":    "Error list",
}

@user.require('root')
def main(cursor, query_filter=""):
    query_filter = common_f.get_val("filter", query_filter)
    
    if query_filter == "":
        error_dict = common_q.get_all(cursor, error.Error, where="fixed = False", orderby="timestamp DESC")
        
    elif query_filter == "today":
        today = datetime.date.today()
        today = time.mktime(today.timetuple())
        error_dict = common_q.get_all(cursor, error.Error, where="timestamp >= %d AND fixed = False" % today, orderby="timestamp DESC")
        
    else:
        error_dict = common_q.get_all(cursor, error.Error, where="mode='%s' and fixed = False" % database_f.escape(query_filter), orderby="timestamp DESC")
    
    output = []
    
    if len(error_dict) > 0:
        user_dict = common_q.get_all(cursor, user.User,)
        user_dict[-1] = user.User(username="Not logged in")
        output.append("""<table border="0" cellspacing="0" cellpadding="5" style="width:100%;">
            <tr class="row2">
                <th>Date</th>
                <th>Mode</th>
                <th>Func Call</th>
                <th>Type</th>
                <th>User</th>
                <th colspan="2">&nbsp;</th>
            </tr>
            """)
        
        i = 1
        for error_id, the_error in error_dict.items():
            i += 1
            
            the_date = the_error.timestamp
            
            output.append("""
            <tr class="row{row}" id="row{error_id}">
                <td>{date}</td>
                <td>{mode}</td>
                <td>{function_call}</td>
                <td>{etype}</td>
                <td>{user}</td>
                <td class="block_cell"><a href="web.py?mode=edit_error&amp;error={error_id}">View</a></td>
                <td class="block_cell"><a href="#" onclick="{onclick}">Fix</a></td>
            </tr>""".format(
                error_id = error_id,
                row      = i % 2,
                etype    = the_error.exception_type,
                date     = common_f.display_date(the_date, "%d of %B at %H:%M"),
                mode     = "No mode specified" if the_error.mode == "" else the_error.mode,
                function_call = "" if the_error.function_call == "" else the_error.function_call,
                user     = user_dict[the_error.user_id].username,
                
                onclick = """$('#ajax_target').load('web.py', {'mode':'edit_error', 'error':'%d', 'sub_mode':'fix'}); $('#row%d').hide(); return false;""" % (error_id, error_id),
            ))
        
        output.append("</table>")
    
    else:
        output.append("<div style='padding:10px;'>No errors found</div>")
    
    modes = {}
    
    # Select all the groups possible
    query = """SELECT mode FROM errors GROUP BY mode"""
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    for row in cursor:
        modes[row['mode']] = row['mode']
    
    page_data['Rows'] = len(error_dict)
    page_data['Title'] = "Error list (%d)" % len(error_dict)
    page_data['Filters'] = """
        <form action="web.py" method="get" accept-charset="utf-8" style="float: left;">
            <a href="web.py?mode=list_errors">All errors</a>
            <a href="web.py?mode=list_errors&amp;filter=today">Todays errors</a>
            
            &nbsp;&nbsp;&nbsp;
            
            <input type="hidden" name="mode" value="list_errors" />
            
            {}
            
            <input type="submit" value="Sort by mode" />
        </form>
    """.format(html_f.option_box("filter", modes, selected=query_filter))
    
    return "".join(output)
