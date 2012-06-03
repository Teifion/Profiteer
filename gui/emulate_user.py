import datetime
from profiteer import error, user, common_q, common_f, web, html_f
import re

from profiteer.test_lib import gui_test_utils

page_data = {
    "Template": "admin",
    "Title":    "Emulate user",
}

def show_form(cursor):
    return """
    <form action="web.py" method="post" accept-charset="utf-8" style="padding:10px;">
        <input type="hidden" name="mode" id="mode" value="emulate_user" />
        
        <table border="0" cellspacing="0" cellpadding="5">
            <tr>
                <td><label for="user_id">User:</label></td>
                <td>{user_id}</td>
            </tr>
            <tr>
                <td><label for="emulate_mode">Mode:</label></td>
                <td><input type="text" name="emulate_mode" id="emulate_mode" value="" /></td>
            </tr>
            <tr>
                <td colspan="2">
                    <input type="submit" value="Emulate" style="width:95%;" />
                </td>
            </tr>
        </table>
    </form>
    """.format(
        user_id = html_f.option_box("user_id", common_q.get_all(cursor, user.User), element_property="username"),
    )

@user.require('root')
def main(cursor, emulate_mode="", user_id=-1, mask_cursor=True):
    user_id      = int(common_f.get_val("user_id", user_id))
    emulate_mode = common_f.get_val("emulate_mode", emulate_mode)
    mask_cursor  = bool(common_f.get_val("mask_cursor", mask_cursor))
    
    if user_id < 1 and emulate_mode == "":
        return show_form(cursor)
    
    if user_id < 1:
        return "No user selected"
    
    if emulate_mode == "":
        return "No mode to emulate"
    
    # Allows us to test the traceback display
    force_error = bool(common_f.get_val("force_error", False))
    if force_error:
        return force_error_func()
    
    # Set ourselves to fake the user that saw the bug
    real_user = common_f.cache['user']
    the_user = common_q.get_one(cursor, user.User, id=user_id)
    common_f.cache['user'] = the_user
    
    output = []
    
    # The two new lines are for our regex
    # the_error.args += "\n\n"
    # re_results = re.findall(r"([a-zA-Z_]*?) = (.*?\n\n)", the_error.args)
    
    # Now build the CGI form
    # cgi_fields = [(k, v.strip()) for k,v in re_results]
    # gui_test_utils.new_cgi_form(cgi_fields)
    
    # Alter the require function to suit our emulation needs
    user.require = error.emulate_require
    
    # Also stop our cursor from altering the database
    if mask_cursor:
        cursor.execute = error.emulate_execute(cursor.execute)
    
    # Lets try importing the page
    try:
        the_page = web.import_page(emulate_mode, handle_exception=False)
    except Exception:
        return "&nbsp;&nbsp; Unable to import page" + error.html_render(headers=False)
    
    # Some variables for displaying stuff
    output.append("""
    <div style="padding:10px;">
        <strong>Emulating:</strong> <a href="?mode=edit_user&amp;user={user_id}">{user}</a>
        &nbsp;&nbsp;&nbsp;
        
        <strong>Mode:</strong> {mode}
        &nbsp;&nbsp;&nbsp;
        
        <a style="float:right;" href="web.py">Your dashboard</a>
    </div>
    <hr>
    <div style='padding:10px;'>
        <span class="stitle">Page output</span><br /><br />
    """.format(
        user = the_user.username,
        user_id = the_user.id,
        mode = emulate_mode,
    ))
    
    # Good good, now lets try executing it
    try:
        page_output = the_page.main(cursor)
    except Exception:
        output.append(error.html_render(headers=False))
    else:
        output.append(page_output)
    finally:
        output.append("</div>")
    
    # Reset the real user
    # common_f.cache['user'] = real_user
    
    return "".join(output)

def force_error_func():
    raise Exception("")
