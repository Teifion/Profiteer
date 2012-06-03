import data
from profiteer import database_f, cli_f, sync_q, sync_f, user, error, user_log

table_list = [
    user.User.table_info,
    error.Error.table_info,
    user_log.UserLog.table_info,
] + data.sync_tables

def main(fix = False, show_fixes=False, print_output=True):
    output = []
    
    # This allows for easy swapping
    if print_output:
        pr = print
    else:
        pr = output.append
    
    cursor = database_f.get_cursor()
    
    if fix: pr(cli_f.shell_text("\n''Checking and fixing tables''"))
    else:   pr(cli_f.shell_text("\n''Checking tables''"))
    
    for table_info in table_list:
        pr(sync_f.check_table(cursor, table_info, fix, show_fixes))
    
    if fix:
        pr("\nCommited changes\n")
    
    if pr == output.append:
        try:
            return "\n".join(output)
        except Exception as e:
            print(output)
            raise
    else:
        return ""
