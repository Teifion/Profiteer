from profiteer import database_f, common_f
from profiteer.gui import pages
import time
import data

import_time = time.time()

excluded_pages = data.excluded_logs

class UserLog (database_f.DBConnectedObject):
    table_info = {
        "Name":         "user_logs",
        "Indexes":      {
            "user_id":  "user_id",
            "page":     "page",
        },
        "Fields":       (
            database_f.SerialField("id",                primary_key=True),
            database_f.IntegerField("user_id"),
            database_f.VarcharField("page",             max_length=60),
            
            database_f.TimestampField("access_time"),
            database_f.DoubleField("load_time"),
        )
    }
    
    def __init__(self, *args, **kwargs):
        if "access_time" not in kwargs:
            kwargs['access_time'] = int(time.time())
        
        super(UserLog, self).__init__(*args, **kwargs)

def log_usage(cursor, override_mode=None):
    if common_f.cache.get("user", None) != None:
        user_id = common_f.cache['user'].id
    else:
        user_id = -1
    
    if not override_mode:
        override_mode = common_f.get_val("mode", pages.default_page)
    
    if override_mode in excluded_pages:
        return
    
    the_log = UserLog(
        user_id         = user_id,
        page            = override_mode,
        access_time     = int(import_time),
        load_time       = time.time() - import_time,
    )
    
    try:
        the_log.insert(cursor)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), the_log.insert(test_mode=True)))

