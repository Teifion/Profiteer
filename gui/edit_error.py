import datetime
from profiteer import error, user, common_q, common_f, edit_f

page_data = {
    "Template": "admin",
    "Title":    "Edit error",
}

@user.require('root')
def main(cursor, error_id = -1):
    error_id = int(common_f.get_val("error", error_id))
    sub_mode = common_f.get_val('sub_mode', "form")
    
    if sub_mode == "fix":
        return fix(cursor, error_id)
    
    if sub_mode == "delete":
        return delete(cursor, error_id)
    
    the_error = common_q.get_one(cursor, error.Error, id=error_id)
    the_user = common_q.get_one(cursor, user.User, id=the_error.user_id)
    
    output = []
    
    http_args = the_error.args.replace("\n\n", "\n").replace(" ", "")
    http_args = "&amp;".join(http_args.split("\n"))
    http_args = http_args.replace("mode=", "emulate_mode=")
    
    output.append("""
        <div style="padding:10px;">
            <span style="float:right;padding-right:20px;">
                <a href="web.py?mode=edit_error&amp;sub_mode=delete&amp;error={error_id}">Delete</a>
            </span>
            
            <a href="web.py?mode=emulate_user&amp;{http_args}&amp;user_id={user_id}">Emulate</a>
            <br><br>
            
            <strong>Time:</strong> {timestamp}
            &nbsp;&nbsp;&nbsp;
            
            <strong>User:</strong> {user}
            &nbsp;&nbsp;&nbsp;
            
            <strong>Mode:</strong> <a href="web.py?mode=list_errors&amp;filter={mode}">{mode}</a>
            <br>
            
            <strong>Data:</strong><br>
            <textarea rows="8" style="width:99%;">{args}</textarea>
        </div>
        <br>
        
        <div style="padding:0px;border-top:1px solid #AAA;">
            {traceback}
        </div>
    """.format(
        error_id = int(error_id),
        user_id = the_user.id,
        user = the_user.username if the_user != None else "Not logged in",
        mode = the_error.mode,
        args = the_error.args,
        http_args = http_args,
        timestamp = common_f.display_date(the_error.timestamp, "%d of %B at %H:%M"),
        traceback = the_error.traceback,
    ))
    
    return "".join(output)

def delete(cursor, error_id):
    the_error = edit_f.delete(cursor, error.Error, id=int(common_f.get_val('error', error_id)))

    page_data['Redirect'] = "web.py?mode=list_errors"
    return ""

def fix(cursor, error_id):
    query = """UPDATE errors SET fixed = 'True' WHERE id = '{:d}';""".format(error_id)
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    page_data['Redirect'] = "web.py?mode=list_errors"
    return ""
