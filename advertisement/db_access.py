from django.db import connection

def dictfetchall(cursor):
    "Return all rows from a cursor as a list of dicts"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

#query to fetch all advertisements
def advertisement(advt_type):
    sql = f"""
        SELECT * 
        FROM advertisement_new 
        WHERE addType = %s AND status_cur != 1 
        ORDER BY id DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql, [advt_type])  
        return dictfetchall(cur)

#query to get all visitors using advertisement id
def get_all_visitors(id, offset=0, limit=10):
    sql = """
        SELECT * 
        FROM visitor 
        WHERE advtid = %s
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """
    with connection.cursor() as cur:
        cur.execute(sql, [id, limit, offset])
        return dictfetchall(cur)

#query to get data from visitor table using ip address 
def get_all_views(ip, offset=0, limit=10):
    sql = """
        SELECT * 
        FROM visitor 
        WHERE ipaddress = %s
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """
    with connection.cursor() as cur:
        cur.execute(sql, [ip, limit, offset])
        return dictfetchall(cur)
