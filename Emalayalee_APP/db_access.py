from django.db import connection
from datetime import datetime
from .utils import fix_mojibake
from .pagination import build_pagination, fetch_paginated_data
from .record_utils import add_full_urls

# Get data from a specific table
def get_paginated_table_data(table_name, page=1, page_size=10, request=None, order_by='date', fix_encoding=True):
    # First: count total records
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_records = cursor.fetchone()[0]

    # If records <= 100 → fetch all without pagination
    if total_records <= 500:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY {order_by} DESC")
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        results = [add_full_urls(row, table_name) for row in results]
        if fix_encoding:
            results = fix_mojibake(results)
        return {
            'total_records': total_records,
            'results': results
        }

    # Else → paginated fetch
    query = f"SELECT * FROM {table_name} ORDER BY {order_by} DESC"
    total_records, results, base_url = fetch_paginated_data(query, [], page, page_size, request)
    results = [add_full_urls(row, table_name) for row in results]
    if fix_encoding:
        results = fix_mojibake(results)

    return {
        'total_records': total_records,
        'page': page,
        'page_size': page_size,
        'results': results,
        **build_pagination(base_url, page, page_size, total_records)
    }

# Get record by ID
def get_record_by_id(table_name, record_id, field_map=None):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", [record_id])
        row = cursor.fetchone()
        columns = [col[0] for col in cursor.description]
        result = dict(zip(columns, row)) if row else None

        if result:
            result = add_full_urls(result,table_name)  # Add full image URLs if applicable

        # Map fields if needed
        if field_map and result:
            result = {field_map.get(k, k): v for k, v in result.items()}
    return result

# get news types list
def get_news_types():
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT newsType FROM newsmalayalam")
        rows = cursor.fetchall()
        if not rows:
            return []
        return [row[0] for row in rows]

# Get news by type
def get_news_by_type(news_type, request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))
    query = "SELECT * FROM newsmalayalam WHERE newsType = %s ORDER BY date DESC"
    total_records, results, base_url = fetch_paginated_data(query, [news_type], page, page_size, request)
    
    results = [add_full_urls(row) for row in results]
    
    return {
        'total_records': total_records,
        'page': page,
        'page_size': page_size,
        'news_type': news_type,
        'results': results,
        **build_pagination(base_url, page, page_size, total_records)
    }
    

# Get news by type & status
def get_news_by_type_and_status(news_type, status_cur, request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))
    query = "SELECT * FROM newsmalayalam WHERE newsType = %s AND status_cur = %s ORDER BY date DESC"
    total_records, results, base_url = fetch_paginated_data(query, [news_type, status_cur], page, page_size, request)

    # Add base URL for images if cdn = 'bunny'
    results = [add_full_urls(row) for row in results]

    return {
        'total_records': total_records,
        'page': page,
        'page_size': page_size,
        'news_type': news_type,
        'status_cur': status_cur,
        'results': results,
        **build_pagination(base_url, page, page_size, total_records)
    }


# Publish news
def update_news_status(news_id, new_status):
    # New status value (0=Published, 1=Deleted, 2=Draft)
    with connection.cursor() as cursor:
        # Fetch existing record
        cursor.execute("SELECT id, newsHde, news FROM newsmalayalam WHERE id = %s", [news_id])
        row = cursor.fetchone()
        if not row:
            return None
        
        news_data = {"id": row[0], "title": row[1], "content": row[2]}
        news_data = fix_mojibake(news_data)

        # Update status
        cursor.execute("UPDATE newsmalayalam SET status_cur = %s WHERE id = %s", [new_status, news_id])
        return news_data
    
# permanently delete news
def permanently_delete_news(news_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM newsmalayalam WHERE id = %s", [news_id]) 
        return {"id": news_id, "status": "deleted"}
        
        
    
# restore news
def restore_news(news_id):
    with connection.cursor() as cursor:
        # Fetch current status first
        cursor.execute("SELECT id, newsHde, news, status_cur FROM newsmalayalam WHERE id = %s", [news_id])
        row = cursor.fetchone()
        if not row:
            return None
        
        current_status = row[3]
        # Decide new status based on current
        if current_status == 1:  # Deleted
            new_status = 0       # Restore to Published
        elif current_status in [2, 3]:  # Draft or Scheduled
            new_status = current_status  # Keep same
        else:
            new_status = current_status  # Already published or other

        # Update status
        cursor.execute("UPDATE newsmalayalam SET status_cur = %s WHERE id = %s", [new_status, news_id])

        restored_news = {"id": row[0], "title": row[1], "content": row[2], "status_cur": new_status}
        restore_news = fix_mojibake(restored_news)
        return restore_news
    
    
# Get slider data
def get_slider_data():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM slider")
        rows = cursor.fetchall()
        if not rows:
            return []
        
        # Convert rows to dict format
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        results = fix_mojibake(results)    
    return results

# add slider data
def update_slider_with_news(slider_id, news_id):
    with connection.cursor() as cursor:
        # Check if news exists
        cursor.execute("SELECT id FROM newsmalayalam WHERE id = %s", [news_id])
        if not cursor.fetchone():
            return False, "News not found"
        
        # Check if slider row exists
        cursor.execute("SELECT id FROM slider WHERE id = %s", [slider_id])
        if not cursor.fetchone():
            return False, "Slider not found"
        
        # Update the slider row
        cursor.execute("UPDATE slider SET newsid = %s WHERE id = %s", [news_id, slider_id])
    return True, "Slider updated with news successfully"

# delete slider
def remove_from_slider(slider_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE slider SET newsid = 0 WHERE id = %s", [slider_id])
    return True

# move news to other newsType
def move_news_to_otherType(news_id, newsType):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE newsmalayalam SET newsType = %s WHERE id = %s", [newsType, news_id])
        
        cursor.execute("SELECT id, newsHde, news FROM newsmalayalam WHERE id = %s", [news_id])
        row = cursor.fetchone()
        if not row:
            return None
        news_data = {"id": row[0], "title": row[1], "content": row[2]}
        news_data = fix_mojibake(news_data)
        return news_data 
    
# copy news to other newsType
def copy_news_records(news_id, newsType):
    with connection.cursor() as cursor:
        # Fetch existing news record
        cursor.execute("SELECT * FROM newsmalayalam WHERE id = %s", [news_id])
        row = cursor.fetchone()
        if not row:
            return None

        columns = [col[0] for col in cursor.description]
        news_data = dict(zip(columns, row))

        # Modify fields for copy
        news_data['newsType'] = newsType
        news_data['copyid'] = news_id
        news_data['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        news_data['upddate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        del news_data['id'] # Remove ID to insert as new record

        # Build dynamic insert
        keys = ", ".join(news_data.keys())
        placeholders = ", ".join(["%s"] * len(news_data))
        values = list(news_data.values())

        cursor.execute(f"INSERT INTO newsmalayalam ({keys}) VALUES ({placeholders})", values)

        return cursor.lastrowid
    
    
    # ------------Social Media Seciton----------------
    
    # mark as posted in social media
def mark_post_as_posted(news_id, account_id, request):
    """Mark a social media post as posted by the logged-in user and return the updated row."""
    user_id = request.user.id if request.user.is_authenticated else None
    user_id = request.user.id
    with connection.cursor() as cursor:
        # Update the post
        cursor.execute("""
            UPDATE social_media_posts 
            SET status = 0, userid = %s, date = NOW() 
            WHERE news_id = %s AND account_id = %s
        """, [user_id, news_id, account_id])

        # Fetch updated row
        cursor.execute("""
            SELECT * FROM social_media_posts 
            WHERE news_id = %s AND account_id = %s
        """, [news_id, account_id])
        row = cursor.fetchone()
        columns = [col[0] for col in cursor.description]
        updated_post = dict(zip(columns, row)) if row else None

    return updated_post

def get_comments_by_status(status, request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))
    query = "SELECT * FROM cmd2 WHERE status = %s ORDER BY date DESC"
    total_records, results, base_url = fetch_paginated_data(query, [status], page, page_size, request)
    
    return {
        'total_records': total_records,
        'page': page,
        'page_size': page_size,
        'status': status,
        'results': results,
        **build_pagination(base_url, page, page_size, total_records)
    }

# Get all blocked IPs
def get_blocked_ips(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 40))
    query = "SELECT id, `blocked-ip`, ip_date FROM ip_address ORDER BY id DESC"
    total_records, results, base_url = fetch_paginated_data(query, [], page, page_size, request)

    return {
        "total_records": total_records,
        "page": page,
        "page_size": page_size,
        "results": results,
        **build_pagination(base_url, page, page_size, total_records)
    }


