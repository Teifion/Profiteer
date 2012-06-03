from profiteer import common_f, database_f, user

page_data = {
    "Headers":  False,
}

@user.require()
def main(cursor):
    table_name      = common_f.get_val("table", "")
    field_name      = common_f.get_val("field", "")
    where           = common_f.get_val("where", "")
    print_query     = common_f.get_val("p", False)
    
    query = """SELECT {field} FROM {table} WHERE {where}""".format(
        table   = table_name,
        field   = field_name,
        where   = where,
    )
    
    if print_query:
        return query
    
    try: cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    for row in cursor:
        return row[field_name]
