from profiteer import common_f, database_f, user

page_data = {
    "Headers":  False,
}

@user.require()
def main(cursor):
    table_name      = common_f.get_val("table", "")
    field_name      = common_f.get_val("field", "")
    new_value       = common_f.get_val("value", "").strip()
    where           = common_f.get_val("where", "")
    print_query     = common_f.get_val("p", False)
    silent          = common_f.get_val("silent", False)
    
    new_value_db = new_value
    try:
        if new_value_db != float(new_value_db) and new_value_db != int(new_value_db):
            new_value_db = "'%s'" % database_f.escape(new_value_db)
    except Exception as e:
        new_value_db = "'%s'" % database_f.escape(new_value_db)
    
    query = """UPDATE {table} SET {field} = {value} WHERE {where};""".format(
        table   = table_name,
        field   = field_name,
        value   = new_value_db,
        where   = where,
    )
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    if print_query:
        return query
    
    if not silent:
        return new_value
    else:
        return ""
