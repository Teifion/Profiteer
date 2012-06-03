from profiteer import common_f, html_f, edit_f, common_q, user
import profiteer.gui.list_users as list_users

page_data = {
    "Template": "admin",
    "Title":    "Edit user",
    "Padding":  10,
}

@user.require('root')
def main(cursor, user_id=-1):
    sub_mode = common_f.get_val('sub_mode', "form")
    
    if sub_mode == "add":
        return add(cursor)
    
    if sub_mode == "commit":
        return commit(cursor)
    
    if sub_mode == "delete":
        return delete(cursor, user_id)
    
    return show_form(cursor, user_id)

def show_form(cursor, user_id):
    user_id = int(common_f.get_val('user', user_id))
    the_user = common_q.get_one(cursor, user.User, id=user_id)
    
    if the_user == None:
        page_data["Padding"] = 0
        return """&nbsp;
        <div class='error'>
            No user selected, listing all users instead.
        </div>
        {}""".format(list_users.main(cursor))
    
    permissions = []
    i = 1
    for p in user.permission_fields:
        if p == "root": continue
        
        # You can't edit attributes you don't have
        if not getattr(common_f.cache['user'], p) and not common_f.cache['user'].root:
            continue
        
        i += 1
        
        permissions.append("""
        <tr class="row{row}">
            <td><label for="{name}">{name}</label></td>
            <td>{value}</td>
        </tr>""".format(
            row   = i % 2,
            name  = p,
            value = html_f.check_box(p, getattr(the_user, p), custom_id=p),
        ))
    
    output = []
    output.append("""
    <form action="web.py" method="post" accept-charset="utf-8">
        <input type="hidden" name="mode" id="mode" value="edit_user" />
        <input type="hidden" name="sub_mode" value="commit" />
        <input type="hidden" name="id" value="{user_id}" />
        <input type="hidden" name="salt" value="{salt}" />
        {root}
        
        Editing: {name_text}
        <br /><br />
        
        <table border="0" cellspacing="5" cellpadding="5">
            <tr>
                <td><label for="password">New password:</label></td>
                <td style="padding: 1px;"><input type="password" name="password" id="password" value="" /></td>
                
                <td width="5">&nbsp;</td>
                
                <td><label for="password2">Confirm password:</label></td>
                <td style="padding: 1px;"><input type="password" name="password2" id="password2" value="" /></td>
            </tr>
            <tr>
                <td colspan="2">
                    <table border="0" cellspacing="0" cellpadding="5">
                        <tr class="row2">
                            <th>Permission</th>
                            <th>Value</th>
                        </tr>
                        {permissions}
                    </table>
                </td>
            </tr>
        </table>
        <br />
        <input type="submit" value="Perform edit" />
    </form>
    <form id="delete_form" action="web.py" method="post" accept-charset="utf-8">
        <input type="hidden" name="user" value="{user_id}" />
        <input type="hidden" name="mode" value="edit_user" />
        <input type="hidden" name="sub_mode" value="delete" />
        <input style="float:right; margin-right:100px;" type="button" value="Delete user" onclick="var answer = confirm('Delete {name_safe}?')
        if (answer) $('#delete_form').submit();" />
    </form>
    {onload}
    <br /><br />""".format(
        user_id     = user_id,
        name_text   = html_f.text_box("name", the_user.username, size=20, custom_id="user_name"),
        
        name_safe   = html_f.js_name(the_user.username),
        onload      = html_f.onload % "$('#user_name').focus();",
        root        = '<input type="hidden" name="root" value="True" />' if the_user.root else "",
        salt        = the_user.salt,
        
        permissions = "".join(permissions),
    ))
    
    page_data['Title'] = "Edit user ({})".format(the_user.username)
    return "".join(output)

def add(cursor):
    the_user = edit_f.add(cursor, user.User)
    
    # Redirect
    page_data['Redirect'] = "web.py?mode=list_users"
    return ""

def commit(cursor):
    the_user = user.User()
    the_user.get_from_form(cursor, common_f.cgi_form.list)
    
    del(the_user.root)
    
    if not common_f.cache['user'].root:
        for p in user.permission_fields:
            if not getattr(common_f.cache['user'], p):
                del(the_user.__dict__[p])
        
    the_user.update(cursor)
    
    # Redirect
    page_data['Redirect'] = "web.py?mode=list_users"
    return ""

def delete(cursor, user_id):
    the_user = edit_f.delete(cursor, user.User, id=int(common_f.get_val('user', user_id)))
    
    page_data['Redirect'] = "web.py?mode=list_users"
    return ""
