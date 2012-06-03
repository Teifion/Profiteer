from profiteer import database_f
import collections

def _query(cursor, class_type, fields="*",
            where = '',
            orderby = '',
            start=0, limit=0, test_mode=False):
    
    if type(class_type) == dict:
        table = class_type['Name']
    else:
        table = class_type.table_info['Name']
    
    query = """SELECT {fields} FROM {table}""".format(
        fields = ",".join(fields),
        table = table,
    )
    
    # Where
    if where != '': query += " WHERE {}".format(where)
    
    # Order by
    if orderby != '': query += " ORDER BY {}".format(database_f.escape(orderby))
    
    # Limit stuff
    if start > 0 and limit > 0: query += " LIMIT {}, {}".format(start, limit)
    if start > 0 and limit < 1: query += " LIMIT 0, {}".format(limit)
    if start < 1 and limit > 0: query += " LIMIT {}".format(limit)
    
    # Test mode?
    if test_mode:
        return query
    
    # Run query
    try:
        cursor.execute(query)
    except Exception as e:
        raise Exception("Database error: %s\nQuery: %s" % (str(e.args[0]).replace("\n",""), query))
    
    # Get results, just 1 field? We want to return a list
    if len(fields) == 1 and type(fields) in (list, tuple):
        results = []
        field_name = fields[0]
        
        for row in cursor:
            results.append(row[field_name])
    
    else:
        if "id" in fields:
            results = collections.OrderedDict()
            for row in cursor:
                results[row['id']] = row
            
        elif fields == "*":
            results = collections.OrderedDict()
            for row in cursor:
                results[row['id']] = class_type(**row)
            
        else:
            raise Exception("")
            results = []
            for row in cursor:
                results.append(row)
    
    # No results?
    if len(results) == 0:
        if limit == 1:
            return None
        else:
            return {}
    
    # If limit is 1 we simple return the first item in our results
    if limit == 1:
        if len(fields) == 1 and type(fields) in (list, tuple):
            return results[0]
        else:
            return results[list(results.keys())[0]]
    
    return results

# A list of ID's
def id_list(cursor, class_type, where='', orderby='id', start=0, limit=0, test_mode=False):
    return _query(cursor, class_type, fields=['id'], where=where, orderby=orderby, start=start, limit=limit, test_mode=test_mode)

def get_all(cursor, class_type, where='', orderby='id', start=0, limit=0, fields="*", test_mode=False):
    return _query(cursor, class_type, where=where, orderby=orderby, fields=fields, start=start, limit=limit, test_mode=test_mode)

# Very similar to get_all but allows a different way to define where
def get_where(cursor, class_type, orderby='id', fields="*", start=0, limit=0, test_mode=False, **wheres):
    where = ""
    if wheres != {}:
        where = []
        for k, v in wheres.items():
            if v == None: continue
            
            # Array handler
            if type(v) in (list, tuple, set):
                if len(v) == 0: continue
                
                safe_vals = []
                
                for i in v:
                    if type(i) == str:
                        safe_vals.append(database_f.escape(i))
                    else:
                        safe_vals.append(str(i))
                
                where.append("%s IN (%s)" % (k, ",".join(safe_vals)))
            
            # Non array
            elif type(v) == str:
                where.append("\"%s\" = '%s'" % (k, database_f.escape(v)))
            elif type(v) in (int, float):
                where.append("\"%s\" = '%s'" % (k, v))
            else:
                raise Exception("No handler for type %s" % type(v))
        
        where = " AND ".join(where)
    
    return _query(cursor, class_type, fields=fields, where=where, orderby=orderby, start=start, limit=limit, test_mode=test_mode)

def get_one(cursor, class_type, where="", test_mode=False, fields="*", orderby="", **wheres):
    if where == "" and wheres != {}:
        where = []
        for k, v in wheres.items():
            if type(v) == str:
                where.append("%s = '%s'" % (k, database_f.escape(v)))
            else:
                where.append("%s = '%s'" % (k, v))
        
        where = " AND ".join(where)
    
    return _query(cursor, class_type, fields=fields, where=where, limit=1, orderby=orderby, test_mode=test_mode)

def get_last(cursor, class_type, fields="*", test_mode=False):
    return _query(cursor, class_type, fields=fields, limit=1, test_mode=test_mode, orderby="id DESC")
