import datetime
import time
from profiteer import user_log, user, common_q, common_f, html_f, database_f

page_data = {
    "Template": "admin",
    "Title":    "User logs",
}

@user.require('root')
def main(cursor, query_filter=""):
    query_filter = common_f.get_val("filter", query_filter)
    
    if query_filter == "":
        log_dict = common_q.get_all(cursor, user_log.UserLog, orderby="access_time DESC")
    
    elif query_filter == "today":
        today = datetime.date.today()
        today = time.mktime(today.timetuple())
        log_dict = common_q.get_all(cursor, user_log.UserLog, where="access_time >= %d" % today, orderby="access_time DESC")
        
    else:
        log_dict = common_q.get_all(cursor, user_log.UserLog, where="mode='%s'" % database_f.escape(query_filter), orderby="access_time DESC")
    
    output = []
    
    if len(log_dict) > 0:
        user_dict = common_q.get_all(cursor, user.User,)
        user_dict[-1] = user.User(username="Not logged in")
        output.append("""<table border="0" cellspacing="0" cellpadding="5" style="width:100%;">
            <tr class="row2">
                <th>Date</th>
                <th>Mode</th>
                <th>User</th>
                <th>Load time</th>
                <th colspan="2">&nbsp;</th>
            </tr>
            """)
        
        i = 1
        for log_id, the_log in log_dict.items():
            i += 1
            
            the_date = the_log.access_time
            
            output.append("""
            <tr class="row{row}">
                <td>{date}</td>
                <td>{page}</td>
                <td>{user}</td>
                <td>{load_time}</td>
                <td class="block_cell"><a href="web.py?mode=edit_log&amp;log={log_id}">View</a></td>
                <td class="block_cell"><a href="web.py?mode=edit_log&amp;log={log_id}&amp;sub_mode=delete">Delete</a></td>
            </tr>""".format(
                log_id    = log_id,
                row       = i % 2,
                load_time = round(the_log.load_time, 4),
                date      = common_f.display_date(the_date, "%d of %B at %H:%M"),
                page      = "No mode specified" if the_log.page == "" else the_log.page,
                user      = user_dict[the_log.user_id].username,
            ))
        
        output.append("</table>")
    
    else:
        output.append("<div style='padding:10px;'>No logs found</div>")
    
    return "".join(output)
