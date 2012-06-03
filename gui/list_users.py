from profiteer import user, common_q, common_f

page_data = {
    "Template": "admin",
    "Title":    "List users",
}

@user.require('root')
def main(cursor):
    if len(user.User.table_info['Fields']) > 10:
        return main_shortform(cursor)
    
    output = []
    
    user_dict = common_q.get_all(cursor, user.User)
    
    output.append("""
    <table border="0" cellspacing="0" cellpadding="5" style="width: 100%;">
        <tr class="row2">
            <th>Name</th>
            <th>Blocked</th>
            {privileges}
            <th>&nbsp;</th>
        </tr>""".format(
            privileges = "".join(["<th>%s</th>" % p.title() for p in user.permission_fields if p != "root"])
        ))
        
    count = -1
    for i, u in user_dict.items():
        count += 1
        
        priviliages = []
        for p in user.permission_fields:
            if p == "root": continue
            if getattr(u, p):
                priviliages.append("<td style='text-align:center;'>&#10004;</td>")
            else:
                priviliages.append("<td>&nbsp;</td>")
        
        output.append("""
        <tr class="row{row}" id="{user_id}">
            <td><strong>{username}</strong></td>
            <td>{blocked}</td>
            {privileges}
            <td class="block_cell"><a href="web.py?mode=edit_user&amp;user={user_id}">Edit</a></td>
        </tr>
        """.format(
            row         = count % 2,
            user_id     = u.id,
            username    = u.username,
            blocked     = "True" if u.blocked else "",
            privileges = "".join(priviliages)
        ))
    
    # Add new user
    count += 1
    output.append("""
    <tr class="row{row}">
        <td>
            <form action="web.py" id="add_user_form" method="post" accept-charset="utf-8">
            <input type="hidden" name="mode" value="edit_user" />
            <input type="hidden" name="sub_mode" value="add" />
            
            <input type="text" id="new_name" name="username" value="" />
        </td>
        <td>
            <input type="password" name="password" id="password" value="" size="10"/>
            <input type="password" name="password2" id="password2" value="" size="10"/>
            <input type="hidden" name="salt" value="{salt}" />
        </td>
        <td colspan="{colspan}">&nbsp;</td>
        <td>
            <input type="submit" value="Add" />
            </form>
        </td>
    </tr>
    """.format(
        row     = count % 2,
        salt    = user.make_salt(),
        colspan = len(user.permission_fields)-1,
    ))
    
    output.append("</table>")
    
    if common_f.get_val('ajax', False):
        output.append("<br /><br />")
    else:
        # output.append(html_f.onload % "$('#new_name').focus();")
        pass
    
    return "".join(output)

# Used when we have a lot of permissions
def main_shortform(cursor):
    output = []
    
    user_dict = common_q.get_all(cursor, user.User)
    
    output.append("""
    <table border="0" cellspacing="0" cellpadding="5" style="width: 100%;">
        <tr class="row2">
            <th>Name</th>
            <th>Blocked</th>
            <th>Privilages</th>
            <th>&nbsp;</th>
        </tr>""")
        
    count = -1
    for i, u in user_dict.items():
        count += 1
        
        priviliages = []
        for p in user.permission_fields:
            if p == "root": continue
            if getattr(u, p):
                priviliages.append("&#10004;")
            else:
                priviliages.append("&nbsp;")
        
        output.append("""
        <tr class="row{row}" id="{user_id}">
            <td><strong>{username}</strong></td>
            <td>{blocked}</td>
            <td>{privileges}</td>
            <td class="block_cell"><a href="web.py?mode=edit_user&amp;user={user_id}">Edit</a></td>
        </tr>
        """.format(
            row         = count % 2,
            user_id     = u.id,
            username    = u.username,
            blocked     = "True" if u.blocked else "",
            privileges = "&nbsp;".join(priviliages)
        ))
    
    # Add new user
    count += 1
    output.append("""
    <tr class="row{row}">
        <td>
            <form action="web.py" id="add_user_form" method="post" accept-charset="utf-8">
            <input type="hidden" name="mode" value="edit_user" />
            <input type="hidden" name="sub_mode" value="add" />
            
            <input type="text" id="new_name" name="username" value="" />
        </td>
        <td>
            <input type="password" name="password" id="password" value="" size="10"/>
            <input type="password" name="password2" id="password2" value="" size="10"/>
            <input type="hidden" name="salt" value="{salt}" />
        </td>
        <td>&nbsp;</td>
        <td>
            <input type="submit" value="Add" />
            </form>
        </td>
    </tr>
    """.format(
        row     = count % 2,
        salt    = user.make_salt().replace('"', "'"),
        colspan = len(user.permission_fields)-1,
    ))
    
    output.append("</table>")
    
    if common_f.get_val('ajax', False):
        output.append("<br /><br />")
    else:
        # output.append(html_f.onload % "$('#new_name').focus();")
        pass
    
    return "".join(output)
