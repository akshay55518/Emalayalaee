from datetime import timedelta, datetime, timezone

from django.contrib.sites import requests
from django.db import connection
from django.views.decorators.csrf import csrf_exempt


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def get_activity():
    query = """
    SELECT * FROM activity_log
    
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        return dictfetchall(cursor)


def get_active_users():
    """
    Fetch distinct user IDs with activity in the last 30 minutes.
    Returns a list of dictionaries containing user IDs.
    """
    try:
        with connection.cursor() as cursor:
            # Calculate time 30 minutes ago using django.utils.timezone
            thirty_minutes_ago = timezone.now() - timedelta(minutes=30)

            # SQL query to get distinct user IDs with recent activity
            cursor.execute("""
                SELECT DISTINCT userid
                FROM activity_log
                WHERE date >= %s
            """, [thirty_minutes_ago])

            # Fetch all results
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            active_users = [{'userid': row[0]} for row in rows]

            return active_users
    except Exception as e:
        raise Exception(f"Error fetching active users: {str(e)}")





# event occurrences graph


# Action code to event name mapping
ACTION_EVENT_MAP = {
    1: "page_view",
    2: "scroll",
    3: "session_start",
    4: "user_engagement",
    5: "first_visit",
    6: "click",
    7: "form_start",
    8: "form_submit",
    9: "file_download",
    10: "video_start",
    11: "video_search_result",
    12: "video_progress",
    13: "video_complete",

}

def get_event_occurrences():
    query = """
        SELECT action, COUNT(*) AS occurrences
        FROM activity_log
        GROUP BY action
        ORDER BY occurrences DESC
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    event_data = []
    for action_code, count in results:
        event_name = ACTION_EVENT_MAP.get(action_code, f"unknown_event_{action_code}")
        event_data.append({
            "event": event_name,
            "count": count
        })

    return event_data



# Events --------------------------------------------


def get_page_views_per_day():
    query = """
        SELECT
            DATE_FORMAT(date, '%Y%m%d') AS formatted_date,
            COUNT(*) AS page_views
        FROM
            activity_log
        WHERE
            action = 1
        GROUP BY
            formatted_date
        ORDER BY
            formatted_date DESC
        LIMIT 8  # To match the ~8 dates shown in your image
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    return [{"date": row[0], "count": row[1]} for row in rows]



# session graph ---------------------------------------------------------


def get_session_data(days=7, date_from=None, date_to=None):
    """
    Fetch session data between dates (format: YYYY-MM-DD)
    Args:
        days: Default days back if no date range provided
        date_from: Start date (optional)
        date_to: End date (optional)
    Returns:
        List of dictionaries with session data
    """
    if not date_from:
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')

    query = """
    SELECT 
        DATE(date) as session_date,
        COUNT(DISTINCT ipaddress) as session_count,
        COUNT(*) as total_events
    FROM visitor
    WHERE date BETWEEN %s AND %s
    GROUP BY session_date
    ORDER BY session_date
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [date_from, date_to])
        return dictfetchall(cursor)


def get_session_metrics():
    """Get key session metrics for the last 7 days"""
    query = """
    SELECT 
        COUNT(DISTINCT ipaddress) as total_sessions,
        COUNT(*) as total_events,
        AVG(events_per_session) as avg_events_per_session
    FROM (
        SELECT 
            ipaddress,
            COUNT(*) as events_per_session
        FROM visitor
        WHERE date >= NOW() - INTERVAL 7 DAY
        GROUP BY ipaddress
    ) as sessions
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        return dictfetchall(cursor)[0]






# Editor -----------------------------------------------------------------------------------------------------

def get_all_admins():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                * FROM admin1;
        """)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]




def delete_admin_by_id(admin_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM admin1 WHERE AdminId = %s", [admin_id])



def update_admin_by_id(admin_id, username, password, admin_type):
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE admin1
            SET Username = %s,
                Password = %s,
                adminType = %s,
                updDate = NOW()
            WHERE AdminId = %s
        """, [username, password, admin_type, admin_id])


@csrf_exempt
def create_admin(username, password, admin_type):
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO admin1 (Username, Password, adminType, date, updDate)
            VALUES (%s, %s, %s, NOW(), NOW())
        """, [username, password, admin_type])







def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None

def get_editor_by_id(admin_id):
    query = """
        SELECT * FROM admin1 WHERE AdminId = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [admin_id])
        return dictfetchone(cursor)




