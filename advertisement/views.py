from .db_access import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import connection
from django.utils.timezone import now
from datetime import date
from Emalayalee_APP.language_utils import fix_mojibake
from Emalayalee_APP.login_authetication import jwt_required
from Emalayalee_APP.pagination import build_pagination, fetch_paginated_data
from Emalayalee_APP.db_access import move_to_resycle_table

#advertisement view
@jwt_required
def advt_view(request, type):
    
    try:    
        allowed = ["TOPBANNER", "HOMERIGHT", "ARTICLEDESKTOP", "ARTICLEMOBILE"]
        if type not in allowed:
            return JsonResponse({"message": "Error", "error": "Invalid advertisement type"}, status=400)


        results = advertisement(type)
        results = fix_mojibake(results)

        return JsonResponse({
            "code": 200,
            "message": "Fetched Successfully",
            "description": "",
            "errors": [],
            "payload": results,
        })

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": "Something went wrong",
            "description": str(e),
            "errors": [str(e)],
            "payload": {}
        }, status=500)


#used in visitors view to add next page urls
def get_total_visitors_count(id):
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM visitor WHERE advtid = %s",[id])
        return cur.fetchone()[0]


#view visitors through advertisement id or direct visitor view
@jwt_required
def visitors_view(request, id):
    try:
        page = int(request.GET.get("page[number]", 1))
        page_size = int(request.GET.get("page[size]", 30))

        query = """
            SELECT * FROM visitor WHERE advtid = %s
        """
        params = [id]

        total, results, base_url = fetch_paginated_data(query, params, page, page_size, request)
        results = fix_mojibake(results)
        pagination = build_pagination(base_url, page, page_size, total)

        response_payload = {
            "visits": total,
            "data": results,
            "links": pagination,
        }

        return JsonResponse({
            "code": 200,
            "message": "Fetched Successfully",
            "description": "",
            "errors": [],
            "payload": response_payload
        })

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": "Something went wrong",
            "description": str(e),
            "errors": [str(e)],
            "payload": {}
        }, status=500)

#used in search by ip address to find cound for url creation
def ip_based_count(ip):
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM visitor WHERE ipaddress = %s",[ip])
        return cur.fetchone()[0]

#ip based search view
@jwt_required
def ip_based_search_view(request, ip):
    try:
        page = int(request.GET.get("page[number]", 1))
        page_size = int(request.GET.get("page[size]", 30))

        query = """
            SELECT * FROM visitor WHERE ipaddress = %s
        """
        params = [ip]

        total, results, base_url = fetch_paginated_data(query, params, page, page_size, request)
        results = fix_mojibake(results)
        pagination = build_pagination(base_url, page, page_size, total)

        response_payload = {
            "visits": total,
            "data": results,
            "links": pagination,
        }

        return JsonResponse({
            "code": 200,
            "message": "Fetched Successfully",
            "description": "",
            "errors": [],
            "payload": response_payload
        })

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": "Something went wrong",
            "description": str(e),
            "errors": [str(e)],
            "payload": {}
        }, status=500)

#query to fetch the advetisement by id
def exist_advt(id):
    select_sql = """
        SELECT * 
        FROM advertisement_new 
        WHERE id = %s
        AND status_cur != 1 
    """
    with connection.cursor() as cur:
        cur.execute(select_sql, [id])
        row = cur.fetchone()
    return row is not None  


#advertisement editing view
@csrf_exempt
@jwt_required
def editing_ad(request, id):
    
    if not exist_advt(id):
        return JsonResponse({"message": "Advertisement not found or inactive"}, status=404)

    if request.method != "PATCH":
        return JsonResponse({"message": "Only PATCH allowed"}, status=405)

    try:
        data = json.loads(request.body.decode())
        allowed = {"name": "name = %s", "advertisement": "image = %s", "url": "url = %s"}

        fields = [sql for key, sql in allowed.items() if key in data]
        params = [data[key] for key in allowed if key in data]

        if not fields:
            return JsonResponse({"message": "No valid fields to update"}, status=400)
        
        sql = f"UPDATE advertisement_new SET {', '.join(fields)} WHERE id = %s AND status_cur != 1"
        params.append(id)
        with connection.cursor() as cur:
            cur.execute(sql, params)
        return JsonResponse({"message": "Updated", "rows": cur.rowcount})
    except Exception as e:
        return JsonResponse({"message": "Error", "error": str(e)}, status=500)


#delete advertisement
@jwt_required
@csrf_exempt
def delete_ad(request, id):
    if request.method == "DELETE":
        try:
            user_id = request.user_id

            if not exist_advt(id):
                return JsonResponse({"message": "Advertisement not found or inactive"}, status=404)

            # Fetch addType before deleting
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT addType FROM advertisement_new WHERE id = %s", [id]
                )
                row = cur.fetchone()
                if not row:
                    return JsonResponse({"message": "Advertisement not found"}, status=404)

                addType = row[0] or "ADVERTISEMENT"  # Fallback if addType is NULL

                # Mark as deleted
                update_sql = """
                    UPDATE advertisement_new 
                    SET status_cur = 1, status_mge = %s
                    WHERE id = %s
                """
                cur.execute(update_sql, [user_id, id])
                rows_affected = cur.rowcount

            # Insert into resycle table
            move_to_resycle_table(
                newsid=id,
                mge=user_id,
                nswstype=addType,
                db="advertisement_new"
            )

            return JsonResponse({
                "message": "Deleted Successfully",
                "rows": rows_affected
            })

        except Exception as e:
            return JsonResponse({"message": "Error", "error": str(e)}, status=500)

    return JsonResponse({"message": "Only DELETE method allowed"}, status=405)


#creating advertisement
@jwt_required
@csrf_exempt
def create_ad(request, type):
    if request.method == "POST":

        try:
            allowed = ["TOPBANNER", "HOMERIGHT", "ARTICLEDESKTOP", "ARTICLEMOBILE"]
            if type not in allowed:
                return JsonResponse({"message": "Error", "error": f"Invalid advertisement type:{type}"}, status = 400)
            
            title = request.POST.get("title")
            image = request.FILES.get("image")  
            url = request.POST.get("url")
            ad_type = type 
            status =  0

            if not all([title, image, url]):
                return JsonResponse({"message": "Missing required fields (title, image, url)"}, status=400)

            #query to add to advertisement_new
            insert_sql = """
                INSERT INTO advertisement_new (addType, name, image, url, status_cur, status_mge, date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = [ad_type, title, image, url, status, status, now()]

            with connection.cursor() as cur:
                cur.execute(insert_sql, params)
                advt_id = cur.lastrowid

            #query to add to cdn_advt_uploads using advt_id from advertisement_new
            insert_sql = """
                INSERT INTO cdn_advt_uploads (advt_id, advt_type, file_name, status, date)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = [advt_id, ad_type, image, status, now()]

            with connection.cursor() as cur:
                cur.execute(insert_sql, params)

            return JsonResponse({"message": "Advertisement created successfully"})

        except Exception as e:
            return JsonResponse({"message": "Error", "error": str(e)}, status=500)

    return JsonResponse({"message": "Only POST method allowed"}, status=405)


#count information displayed in the home part
@jwt_required
def home_count_view(request):

    try:
        with connection.cursor() as cur:
            # Get total articles
            cur.execute("SELECT COUNT(*) FROM newsmalayalam WHERE status_cur = 0")
            articles = cur.fetchone()[0]

            # Get last status_mge and date and id
            cur.execute("""
                SELECT status_mge, date, id
                FROM newsmalayalam
                WHERE status_mge != 0 AND status_cur = 0
                ORDER BY date DESC
                LIMIT 1
            """)
            status_mge = None
            last_updated_date = None
            last_updated_id = None

            last_status_mge_row = cur.fetchone()
            if last_status_mge_row:
                status_mge = last_status_mge_row[0] 
                last_updated_date = last_status_mge_row[1] 
                last_updated_id = last_status_mge_row[2]

            # Get user who last updated
            last_updated_user = None
            if status_mge:
                cur.execute("SELECT Username FROM admin1 WHERE Adminid = %s", [status_mge])
                last_updated_row = cur.fetchone()
                last_updated_user = last_updated_row[0] if last_updated_row else None

            # Get today's new articles
            today = date.today()
            cur.execute("SELECT COUNT(*) FROM newsmalayalam WHERE status_cur = 0 AND DATE(date) = %s", [today])
            new_articles = cur.fetchone()[0]

        response_payload = {
            "articles_published": articles,
            "new_articles_today": new_articles,
            "last_updated_article": last_updated_id,
            "last_updated_by": last_updated_user,
            "last_updated_date": str(last_updated_date) if last_updated_date else None,
        }

        return JsonResponse({
            "code": 200,
            "message": "Fetched Successfully",
            "description": "",
            "errors": [],
            "payload": response_payload
        })

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": "Something went wrong",
            "description": str(e),
            "errors": [str(e)],
            "payload": {}
        }, status=500)

#articles published today
def articles_today(request):

    try:
        today = date.today()

        with connection.cursor() as cur:
            cur.execute("SELECT * FROM newsmalayalam WHERE status_cur = 0 AND DATE(`date`) = %s", [today])
            results = cur.fetchall()
            columns = [col[0] for col in cur.description]
            data = [dict(zip(columns, row)) for row in results]

            data = fix_mojibake(data)

        if not data:
            return JsonResponse({
                "code": 204,
                "message": "No articles found for today",
                "description": "",
                "errors": [],
                "payload": {"data": []}
            }, status=200)

        response_payload = {
            "data": data,
        }

        return JsonResponse({
            "code": 200,
            "message": "Fetched Successfully",
            "description": "",
            "errors": [],
            "payload": response_payload
        })

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": "Something went wrong",
            "description": str(e),
            "errors": [str(e)],
            "payload": {}
        }, status=500)
