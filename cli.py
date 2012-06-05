import unittest
import os
import sys
import argparse
from profiteer import common_f, database_f, cli_f, config, covers, user
from profiteer import sync as sync_module
import datetime

# Padding
padding = "".join([" " for x in range(0, 8*1024)])

# Function dictionary
func_dict = {}

# Sometimes it's nice to have each output start on a clean screen
if __name__ == '__main__':
    if config.get("clean_screen"):
        os.system('clear')

def tests(options):
    from profiteer import tests as profiteer_tests
    
    profiteer_tests.setup_test_db()
    
    suite = unittest.TestLoader()
    suite = suite.discover(sys.path[0], pattern="*_test.py")
    
    test_program = unittest.TextTestRunner().run(suite)
    
    if test_program.failures == [] and test_program.errors == []:
        module_skip = ['bpgsql3', 'cli', 'sync', 'tests', 'ploc', 'cli_f']
        dirs_skip = ['checks', 'test_lib', 'prof_site', 'data_lists']
        
        if options.verbose:
            output_mode = "print"
        else:
            output_mode = "summary"
        
        covers.get_coverage(
            suite=suite,
            test_program=test_program,
            root_dir=config.get('file_path'),
            verbose=options.all,
            module_skip = module_skip,
            dirs_skip = dirs_skip,
            output_mode=output_mode)

def sync(options, fix=False):
    if options.verbose:
        print(sync_module.main(fix=fix, show_fixes=True))
    else:
        print(sync_module.main(fix=fix))

def profile(options):
    from profile_library import profiler
    
    try:
        x = options.suite
    except Exception:
        print("No suite supplied to profile, select with -s")
        exit()
    
    if options.verbose:
        profiler.view(options)
    else:
        profiler.run(options)

def backup(options):
    """Backs up the database"""
    file_path = "{}/backup/{}_{}_{}.sql".format(
        sys.path[0],
        datetime.date.today().day,
        datetime.date.today().month,
        datetime.date.today().year,
    )
    args = "-h {host} -U {user} {db}".format(
        host = config.get("db_host"),
        user = config.get("db_username"),
        db = config.get("db_name")
    )
    
    os.system("/Library/PostgreSQL/bin/pg_dump {} -f {}".format(args, file_path))
    
    if options.verbose:
        print(cli_f.shell_text("[g]Database backed up[/g]"))
    
    return file_path

def list_modes(options):
    m_list = list(func_dict.keys())
    m_list.sort()
    
    for k in m_list:
        info = func_dict[k][1]
        
        print("{0}: {1}".format(k, info))
    
    print("")

def replicate(options):
    # First we backup the live one
    file_path = backup(options)
    
    connect_string = "-h {host} -U {user}".format(
        host    = config.get("mock_db_host"),
        user    = config.get("mock_db_username"),
    )
    
    # Now we drop the mock one
    os.system("dropdb {} {}".format(connect_string, config.get("mock_db_name")))
    
    # Create a new one
    os.system("createdb {} {}".format(connect_string, config.get("mock_db_name")))
    
    os.system("psql {conn} -d {db_name} -f {path}".format(
        conn    = connect_string,
        db_name = config.get("mock_db_name"),
        path    = file_path,
    ))

def install(options):
    from profiteer import sync as sync_module
    
    """Installs the system"""
    
    # Setup database connection
    if config.get('db_username') == "username":
        if config.get('db_password') == "password":
            print(cli_f.shell_text("[y]No database login[/y]"))
            print("""
Access to the database has not yet been setup. Open config.json and fill in
values for db_host, db_username, db_password and db_name.
            
You can optionally also create values for test and mock databases too. These
will allow you to run unit tests involving the database and to trial code
against mock data.

When ready, run this program again.""")
            
            return False
    
    # Test database connection
    try:
        cursor = database_f.get_cursor()
    except Exception:
        print(cli_f.shell_text("[r]Database not accessible[/r]"))
        print("""
The login details for the database are incorrect. Double check the db_host,
db_username, db_password and db_name fields in config.json

When ready, run this program again to retry the connection.""")
        return False
    
    print(cli_f.shell_text("[g]Connected to database[/g]"))
    
    # Install database
    o = sync_module.main(fix=True, show_fixes=False, print_output=False)
    
    # Insert admin
    query = """UPDATE users SET password = '{}' WHERE id = 1;""".format(user.encode_password('password', 'K*WJgU&j8M) ZT?=J_T-TUfH9*lY#!>@'))
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    print(cli_f.shell_text("[g]Database installed[/g]"))
    
    return True


func_dict = {
    "list":     (list_modes, "List available modes", (), {}),
    "help":     (list_modes, "List available modes", (), {}),
    
    # Maintainance
    "test":     (tests, "Execute unit tests\n  Modes: v a", (), {}),
    
    "sync":     (sync, "Sync the database", (), {}),
    "fix":      (sync, "Update database structure", (), {"fix":True}),
    
    "profile":  (profile, "Run profiler", (), {}),
    "backup":   (backup, "Run backup tool", (), {}),
    "dupe":     (replicate, "Duplicate the live data into the mock database", (), {}),
    
    # Misc
    "install":  (install, "Runs an initial installation", (), {}),
}


def main():
    if config.get("clean_screen"):
        os.system('clear')
    
    parser = argparse.ArgumentParser(description='Arl command line interface.', prog="arl")
    parser.add_argument('m', help='the mode being run with, list modes with mode set to "list"')
    parser.add_argument('-v', dest="verbose", action="store_true", help='Verbose mode')
    parser.add_argument('-a', dest="all", action="store_true", help='all mode means everything is run', required=False)
    parser.add_argument('-live', dest="live", action="store_true", help='live mode for turns', required=False)
    
    args = parser.parse_args()
    
    # Try the func dict
    if args.m.lower() in func_dict:
        f, info, a, k = func_dict[args.m.lower()]
        
        f(args, *a, **k)
    else:
        if args.m == "":
            exit()
        
        # Standard mode
        try:
            print("No mode of {} found".format(args.m))
            f, info, a, k = func_dict["default"]
            f(args, *a, **k)
        except KeyboardInterrupt:
            exit("Exiting from keyboard interrupt")
