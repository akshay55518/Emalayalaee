from django.db import connection

def dictfetchall(cursor):
    "Return all rows from a cursor as a list of dicts"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

#query to fetch all advertisements
def advertisement(advt_type):
    ads_sql = """
        SELECT id, addType, name, image, url
        FROM advertisement_new 
        WHERE addType = %s AND status_cur != 1 
        ORDER BY id DESC
    """

    # Total clicks
    clicks_sql = """
        SELECT advtid, COUNT(*) AS total_clicks
        FROM visitor_new
        GROUP BY advtid
    """

    # Unique clicks
    unique_clicks_sql = """
        SELECT advtid, COUNT(DISTINCT ipaddress) AS unique_clicks
        FROM visitor_new
        GROUP BY advtid
    """

    with connection.cursor() as cur:
        cur.execute(ads_sql, [advt_type])
        ads = dictfetchall(cur)

        cur.execute(clicks_sql)
        total_clicks = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute(unique_clicks_sql)
        unique_clicks = {row[0]: row[1] for row in cur.fetchall()}

    # Add click stats to each ad
    for ad in ads:
        ad_id = ad['id']
        ad['total_clicks'] = total_clicks.get(ad_id, 0)
        ad['unique_clicks'] = unique_clicks.get(ad_id, 0)

    return ads

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
