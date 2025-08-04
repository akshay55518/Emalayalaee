from .db_access import *
from django.http import JsonResponse
from math import ceil
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import connection
from django.utils.timezone import now
from ftfy import fix_text
from rest_framework.views import APIView
from rest_framework.response import Response
import jwt
from datetime import datetime, timedelta, date
from django.conf import settings
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

#login view
class LoginView(APIView):
    def post(self, request):
        username = request.data.get("Username")
        password = request.data.get("Password")

        with connection.cursor() as cursor:
            cursor.execute("SELECT Adminid, Password FROM admin1 WHERE Username = %s", [username])
            row = cursor.fetchone()

        if not row:
            return Response({"error": "Invalid credentials"}, status=401)

        user_id, db_password = row

        # TODO: Use hashed password check in production
        if password != db_password:
            return Response({"error": "Invalid credentials"}, status=401)

        now = datetime.utcnow()
        access_payload = {
            'user_id': user_id,
            'iat': now,
            'exp': now + timedelta(days=30)
        }
        refresh_payload = {
            'user_id': user_id,
            'iat': now,
            'exp': now + timedelta(days=60)
        }

        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

        return Response({
            'access': access_token,
            'refresh': refresh_token
        })

#used for malayalam datas translation
def fix_mojibake(data):
    def fix_dict(d):
        return {k: fix_text(v) if isinstance(v, str) else v for k, v in d.items()}

    if isinstance(data, list):
        return [fix_dict(item) for item in data]
    elif isinstance(data, dict):
        return fix_dict(data)
    else:
        return data


#advertisement view
def advt_view(request, type):
    user_id = login_check(request)
    
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

#check whether user is logged in
def login_check(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"detail": "Authorization header missing or malformed"}, status=401)
    token = auth_header.split(' ')[1].strip()

    try:
        # Decode token using the secret key and algorithm used in login
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except ExpiredSignatureError:
        return JsonResponse({"detail": "Token has expired"}, status=401)
    except InvalidTokenError:
        return JsonResponse({"detail": "Invalid token"}, status=401)

    # You can access user_id from payload if needed
    user_id = payload.get('user_id')
    if not user_id:
        return JsonResponse({"detail": "Invalid token payload"}, status=401)
    return user_id


#view visitors through advertisement id or direct visitor view
def visitors_view(request, id):
    
    user_id = login_check(request)

    try:
        page = int(request.GET.get("page[number]", 1))
        page_size = int(request.GET.get("page[size]", 30))
        offset = (page - 1) * page_size

        total = get_total_visitors_count(id)
        total_pages = ceil(total / page_size)

        results = get_all_visitors(limit=page_size, offset=offset, id=id)
        results = fix_mojibake(results)
        API_BASE_URL = f"http://127.0.0.1:8000/advt/visitor/{id}/"

        response_payload = {
            "visits": total,
            "data": results,
            "links": links(page, total_pages, page_size, total, API_BASE_URL),
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


#used to create urls to next pages
def links(current_page, total_pages, page_size, total_records, API_BASE_URL):
    links = {
        "first": f"{API_BASE_URL}?page[number]=1&page[size]={page_size}",
        "previous": None if current_page <= 1 else f"{API_BASE_URL}?page[number]={current_page - 1}&page[size]={page_size}",
        "next": None if current_page >= total_pages else f"{API_BASE_URL}?page[number]={current_page + 1}&page[size]={page_size}",
        "last": f"{API_BASE_URL}?page[number]={total_pages}&page[size]={page_size}"
    }

    pages = []

    def add_page(p):
        pages.append({
            "page": p,
            "url": f"{API_BASE_URL}?page[number]={p}&page[size]={page_size}",
            "is_active": (p == current_page)
        })

    if total_pages <= 15:
        for p in range(1, total_pages + 1):
            add_page(p)
    else:
        if current_page <= 7:
            for p in range(1, 11):
                add_page(p)
            pages.append({"page": "…"})
            add_page(total_pages - 1)
            add_page(total_pages)
        elif current_page >= total_pages - 6:
            add_page(1)
            add_page(2)
            pages.append({"page": "…"})
            for p in range(total_pages - 9, total_pages + 1):
                add_page(p)
        else:
            add_page(1)
            add_page(2)
            pages.append({"page": "…"})
            for p in range(current_page - 3, current_page + 4):
                add_page(p)
            pages.append({"page": "…"})
            add_page(total_pages - 1)
            add_page(total_pages)

    meta = {
        "current_page": current_page,
        "total_pages": total_pages,
        "page_size": page_size,
        "total_records": total_records
    }

    return {
        "links": links,
        "pages": pages,
        "meta": meta
    }


#used in search by ip address to find cound for url creation
def ip_based_count(ip):
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM visitor WHERE ipaddress = %s",[ip])
        return cur.fetchone()[0]

#ip based search view
def ip_based_search_view(request, ip):
    user_id = login_check(request)
    
    try:
        page = int(request.GET.get("page[number]", 1))
        page_size = int(request.GET.get("page[size]", 30))
        offset = (page - 1) * page_size

        total = ip_based_count(ip)
        total_pages = ceil(total / page_size)

        results = get_all_views(limit=page_size, offset=offset, ip=ip)
        results = fix_mojibake(results)

        response_payload = {
            "visits":total,
            "data": results,
        }

        if(total_pages != 1):
            API_BASE_URL = f"http://127.0.0.1:8000/advt/search/{ip}/"
            response_payload["links"]= links(page, total_pages, page_size, total, API_BASE_URL)


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
def editing_ad(request, id):
    user_id = login_check(request)
    
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
@csrf_exempt
def delete_ad(request, id):
    if request.method == "DELETE":
        try:
            user_id = login_check(request)

            if not exist_advt(id):
                return JsonResponse({"message": "Advertisement not found or inactive"}, status=404)

            update_sql = """
                UPDATE advertisement_new 
                SET status_cur = 1, status_mge = %s
                WHERE id = %s
            """
            with connection.cursor() as cur:
                cur.execute(update_sql, [user_id, id])
                rows_affected = cur.rowcount

            return JsonResponse({
                "message": "Deleted Successfully",
                "rows": rows_affected
            })

        except Exception as e:
            return JsonResponse({"message": "Error", "error": str(e)}, status=500)

    return JsonResponse({"message": "Only DELETE method allowed"}, status=405)


#creating advertisement
@csrf_exempt
def create_ad(request, type):
    if request.method == "POST":
        user_id = login_check(request)
    
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
def home_count_view(request):
    user_id = login_check(request)

    if isinstance(user_id, JsonResponse):
        return user_id

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
    user_id = login_check(request)

    if isinstance(user_id, JsonResponse):
        return user_id

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
