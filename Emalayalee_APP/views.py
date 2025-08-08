from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date
from django.utils.timezone import now

from .db_access import *
from .language_utils import fix_mojibake
from .login_authetication import jwt_required
from .db_access import mark_post_as_posted
from django.http import JsonResponse
import json
import os


# -------- Helper for pagination ----------
def get_paginated_list(request, table_name, order_by):
    page = int(request.GET.get("page[number]", request.GET.get("page", 1)))
    page_size = int(request.GET.get("page[size]", request.GET.get("page_size", 15)))
    data = get_paginated_table_data(
        table_name, page=page, page_size=page_size, request=request, order_by=order_by
    )
    # Fix encoding for results only
    data['results'] = fix_mojibake(data['results'])
    return JsonResponse(data, safe=False, json_dumps_params={"ensure_ascii": False})


# -------- Full data API endpoints --------
@jwt_required
def get_news(request):
    user_id = getattr(request, "user_id", None)
    if not user_id:
        raise ValueError("User ID is missing. Did you forget to protect the route with @jwt_required?")
    return get_paginated_list(request, "newsmalayalam", order_by="id")

@jwt_required
def get_comments(request):
    return get_paginated_list(request, "cmd2", order_by="id")


# def advertise(request):
#     return get_paginated_list(request, "advertisement_new", order_by="id")

@jwt_required
def get_comments_for_record(record_id, table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, email, cmd as comment, date, ip_address, status "
            "FROM cmd2 WHERE newsid = %s AND newsType = %s ORDER BY date DESC",
            [record_id, table_name]
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        comments = [dict(zip(columns, row)) for row in rows]
    return fix_mojibake(comments)


# -------- Fetch data by ID --------
@jwt_required
def get_record_by_id_view(request, table_name, record_id, field_map=None):
    record = get_record_by_id(table_name, record_id, field_map)
    if not record:
        return JsonResponse({
            "code": 404,
            "message": f"{table_name.capitalize()} not found",
            "description": "",
            "errors": ["Record not found"],
            "payload": None
        }, status=404, json_dumps_params={"ensure_ascii": False})
    
    data = fix_mojibake(record)
    
    # Add related comments (for news and charamam)
    if table_name in ["newsmalayalam", "charamam"]:
        data["comments"] = get_comments_for_record(record_id, table_name)

    return JsonResponse({
        "code": 200,
        "message": "Fetched Successfully",
        "description": "",
        "errors": [],
        "payload": data
    }, safe=False, json_dumps_params={"ensure_ascii": False})

@jwt_required
def get_news_by_id_views(request, news_id):
    return get_record_by_id_view(
        request,
        "newsmalayalam",
        news_id,
        {
            "id": "id",
            "newsType": "newsType",
            "title": "newsHde",
            "content": "news",
            "date": "date",
            "author": "name",
            "image_url": "images",
        },
    )

@jwt_required
def get_comments_by_id_views(request, id):
    return get_record_by_id_view(
        request,
        "cmd2",
        id,
        {
            "id": "id",
            "name": "name",
            "comment": "cmd",
            "email": "email",
            "date": "date",
            "news_id": "newsid",
            "newsType": "newsType",
            "status": "status",
            "newsid": "newsid",
        },
    )

# -------- News types --------
@jwt_required
def get_news_types_views(request):
    news_types = get_news_types()
    if not news_types:
        return JsonResponse({"error": "No news types found"}, status=404)
    return JsonResponse(
        news_types, safe=False, json_dumps_params={"ensure_ascii": False}
    )


# -------- News by type --------
@jwt_required
def get_news_by_type_views(request, news_type):
    data = get_news_by_type(news_type, request)
    if not data["results"]:
        return JsonResponse(
            {"error": f"No news found for type '{news_type}'"}, status=404
        )
    data["results"] = fix_mojibake(data["results"])
    return JsonResponse(data, safe=False)


# -------- News by type & status --------
@jwt_required
def get_news_by_type_and_status_views(request, news_type, status_cur):
    data = get_news_by_type_and_status(news_type, status_cur, request)
    if not data["results"]:
        return JsonResponse({"error": "No news found"}, status=404)
    data["results"] = fix_mojibake(data["results"])
    return JsonResponse(data, safe=False, json_dumps_params={"ensure_ascii": False})


# -------- Publish / Delete / Restore / Permanent delete --------
@jwt_required
@csrf_exempt
def publish_news_view(request, news_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    updated = update_news_status(news_id, 0)
    if updated:
        return JsonResponse(
            {"message": "News published successfully", "updated_news": updated},
            status=200,
        )
    return JsonResponse({"error": "News not found"}, status=404)


@csrf_exempt
@jwt_required
def delete_news_view(request, news_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    deleted = update_news_status(news_id, 1)
    if deleted:
        return JsonResponse(
            {"message": "News deleted successfully", "deleted_news": deleted},
            status=200,
        )
    return JsonResponse({"error": "News not found"}, status=404)


@csrf_exempt
@jwt_required
def permanently_delete_news_view(request, news_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    deleted = permanently_delete_news(news_id)
    if deleted:
        return JsonResponse(
            {
                "message": "News permanently deleted successfully",
                "deleted_news": deleted,
            },
            status=200,
        )
    return JsonResponse({"error": "News not found"}, status=404)


@csrf_exempt
@jwt_required
def restore_news_view(request, news_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    restored = restore_news(news_id)
    if restored:
        return JsonResponse(
            {"message": "News restored successfully", "restored_news": restored},
            status=200,
        )
    return JsonResponse({"error": "News not found"}, status=404)


# -------- Add / Edit news --------
@jwt_required
@csrf_exempt
def add_news_view(request, newsType=None):  # <-- Capture from URL
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # Prefer URL param over POST
        newsType = newsType or request.POST.get("newsType")
        if not newsType:
            return JsonResponse({"error": "newsType is required"}, status=400)

        newsHde = request.POST.get("newsHde")
        news = request.POST.get("news")
        language = request.POST.get("language")
        name = request.POST.get("byline")

        # Validate required fields
        required_fields = {
            "newsType": newsType,
            "newsHde": newsHde,
            "news": news,
        }
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            return JsonResponse({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }, status=400)

        # Remaining fields
        images2 = request.POST.get("images2", "")
        news2 = request.POST.get("content", "")
        images = request.POST.get("images", "")
        fdfNte = request.POST.get("fdfNte", "")
        top = request.POST.get("top", 0)
        slider = request.POST.get("slider", 0)
        imgVisibility = request.POST.get("imgVisibility")
        status_cur = request.POST.get("status_cur", 0)
        status_mge = getattr(request, "user_id", None)
        copy = request.POST.get("copy")
        copyid = request.POST.get("copyid")
        writer = request.POST.get("writer")
        facebook_pubstatus = request.POST.get("facebook_pubstatus")
        fbprofile_pubstatus = request.POST.get("fbprofile_pubstatus")
        fbprofile2_pubstatus = request.POST.get("fbprofile2_pubstatus")
        tag = request.POST.get("tag")
        thumbimage = request.POST.get("thumbimage")
        disable_comments = 0 if request.POST.get("disable") else 1
        paid = 0 if request.POST.get("premium_read") else 1
        cdn = request.POST.get("cdn")
        scheduled_at = request.POST.get("scheduled_at")
        content_type = request.POST.get("content_type", "text")
        video_type = request.POST.get("video_type")
        video_url = request.POST.get("video_url")

        # File uploads (same as before)
        pdf_file = request.FILES.get("pdf_file")
        pdf_path = None
        if pdf_file:
            pdf_path = f"uploads/pdf/{pdf_file.name}"
            os.makedirs(os.path.dirname(f"media/{pdf_path}"), exist_ok=True)
            with open(f"media/{pdf_path}", "wb+") as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)

        uploaded_files = request.FILES.getlist("multi_images")
        image_paths = []
        for file in uploaded_files:
            file_path = f"uploads/{file.name}"
            os.makedirs(os.path.dirname(f"media/{file_path}"), exist_ok=True)
            with open(f"media/{file_path}", "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            image_paths.append(file_path)
        
        images = "@*@".join(image_paths)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # DB Insert (same as before)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO newsmalayalam (
                    newsType, newsHde, news, images2, name, news2, images, pdf,
                    fdfNte, language, date, top, slider, upddate, imgVisibility,
                    status_cur, status_mge, copy, copyid, writer,
                    facebook_pubstatus, fbprofile_pubstatus, fbprofile2_pubstatus,
                    tag, thumbimage, disable_comments, paid, cdn, scheduled_at,
                    content_type, video_type, video_url
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                [
                    newsType, newsHde, news, images2, name, news2, ",".join(image_paths), pdf_path,
                    fdfNte, language, date, top, slider, date, imgVisibility, status_cur,
                    status_mge, copy, copyid, writer, facebook_pubstatus,
                    fbprofile_pubstatus, fbprofile2_pubstatus, tag, thumbimage,
                    disable_comments, paid, cdn, scheduled_at, content_type, video_type, video_url
                ],
            )
            last_id = cursor.lastrowid

            cursor.execute("SELECT * FROM newsmalayalam WHERE id = %s", [last_id])
            row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            new_record = dict(zip(columns, row))

        return JsonResponse({
            "message": "News added successfully",
            "data": new_record
        }, json_dumps_params={"ensure_ascii": False})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# edit news
@jwt_required
@csrf_exempt
def edit_news_view(request, news_id):
    if request.method == "GET":
        # Fetch existing news by ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM newsmalayalam WHERE id = %s", [news_id])
            row = cursor.fetchone()

            if not row:
                return JsonResponse({"error": "News not found"}, status=404)

            # Get column names
            columns = [col[0] for col in cursor.description]
            news_data = dict(zip(columns, row))

        return JsonResponse(
            news_data, json_dumps_params={"ensure_ascii": False}, safe=False
        )

    elif request.method == "PATCH":
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = {
            "newsType": request.POST.get("newsType"),
            "newsHde": request.POST.get("heading"),
            "news": request.POST.get("news"),
            "images2": request.POST.get("images2", ""),
            "name": request.POST.get("name"),
            "news2": request.POST.get("content", ""),
            "images": request.POST.get("images", ""),
            "fdfNte": request.POST.get("fdfNte", ""),
            "language": request.POST.get("language", "ml"),
            "top": request.POST.get("top", 0),
            "slider": request.POST.get("slider", 0),
            "upddate": date_now,
            "imgVisibility": request.POST.get("imgVisibility"),
            "status_cur": request.POST.get("status_cur", 0),
            "status_mge": getattr(request, "user_id", None),
            "copy": request.POST.get("copy"),
            "copyid": request.POST.get("copyid"),
            "writer": request.POST.get("writer"),
            "facebook_pubstatus": request.POST.get("facebook_pubstatus"),
            "fbprofile_pubstatus": request.POST.get("fbprofile_pubstatus"),
            "fbprofile2_pubstatus": request.POST.get("fbprofile2_pubstatus"),
            "tag": request.POST.get("tag"),
            "thumbimage": request.POST.get("thumbimage"),
            "disable_comments": 0 if request.POST.get("disable") else 1,
            "paid": 0 if request.POST.get("premium_read") else 1,
            "cdn": request.POST.get("cdn", ""),
            "scheduled_at": request.POST.get("scheduled_at"),
            "content_type": request.POST.get("content_type", "text"),
            "video_type": request.POST.get("video_type"),
            "video_url": request.POST.get("video_url"),
        }

        # Handle file uploads
        pdf_file = request.FILES.get("pdf_file")
        if pdf_file:
            pdf_path = f"uploads/pdf/{pdf_file.name}"
            with open(f"media/{pdf_path}", "wb+") as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
            fields["pdf"] = pdf_path

        uploaded_files = request.FILES.getlist("multi_images")
        if uploaded_files:
            image_paths = []
            for file in uploaded_files:
                file_path = f"uploads/{file.name}"
                with open(f"media/{file_path}", "wb+") as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                image_paths.append(file_path)
            fields["images"] = ",".join(image_paths)

        # Build dynamic SQL
        set_clause = ", ".join([f"`{col}`=%s" for col in fields.keys()])
        values = list(fields.values())
        values.append(news_id)

        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE newsmalayalam SET {set_clause} WHERE id = %s", values
            )

        return JsonResponse(
            {
                "message": "News updated successfully",
                "id": news_id,
                "updated_fields": fields,
            },
            json_dumps_params={"ensure_ascii": False},
        )

    return JsonResponse({"error": "Method not allowed"}, status=405)


# -------- Search news --------
@jwt_required
def search_news_views(request, title):
    if not title:
        return JsonResponse({"error": "Title parameter is required"}, status=400)

    # If title is numeric, fetch by ID (fast, no pagination)
    if title.isdigit():
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM newsmalayalam WHERE id = %s", [int(title)])
            row = cursor.fetchone()
            if not row:
                return JsonResponse({"error": "No news found"}, status=404)
            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, row))
        result = fix_mojibake([result])[0]
        return JsonResponse(
            {"result": result}, 
            json_dumps_params={"ensure_ascii": False}, 
            status=200
        )

    # If not numeric, perform text search with pagination
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))
    query = "SELECT * FROM newsmalayalam WHERE newsHde LIKE %s OR news LIKE %s ORDER BY date DESC"
    search_term = f"%{title}%"
    params = [search_term, search_term]

    total_records, results, base_url = fetch_paginated_data(
        query, params, page, page_size, request
    )

    if not results:
        return JsonResponse({"error": "No news found"}, status=404)

    results = fix_mojibake(results)
    return JsonResponse(
        {
            "total_records": total_records,
            "page": page,
            "page_size": page_size,
            "results": results,
            **build_pagination(base_url, page, page_size, total_records),
        },
        json_dumps_params={"ensure_ascii": False},
    )



# -------- Move / Copy news --------
@csrf_exempt
@jwt_required
def move_news_to_newsType_view(request, news_id, newsType):
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    moved = move_news_to_otherType(news_id, newsType)
    if moved:
        return JsonResponse(
            {"message": "News moved successfully", "moved_news": moved}, status=200
        )
    return JsonResponse({"error": "News not found or move failed"}, status=404)


@csrf_exempt
@jwt_required
def copy_news_view(request, news_id, newsType):
    if request.method != "PATCH":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    new_id = copy_news_records(news_id, newsType)
    if not new_id:
        return JsonResponse({"error": "Original news not found"}, status=404)
    return JsonResponse(
        {
            "message": f"News {news_id} copied to {newsType} with new ID {new_id}",
            "new_id": new_id,
        }
    )

# -------- Social Media --------
@jwt_required
def get_today_post_count(request):
    today = now().strftime("%Y-%m-%d")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM social_media_posts WHERE DATE(date) = %s AND status = 0",
            [today],
        )
        count = cursor.fetchone()[0]
    return JsonResponse({"today_social_post_count": count})

@jwt_required
def mark_as_posted_view(request, news_id, account_id):
    updated_post = mark_post_as_posted(news_id, account_id, request)
    if not updated_post:
        return JsonResponse({"error": "Post not found"}, status=404)
    return JsonResponse({"success": True, "post": updated_post})


# -------- comments --------
# view all comments with pagination
@jwt_required
def get_comments_by_status_views(request, status):
    data = get_comments_by_status(status, request)
    if not data["results"]:
        return JsonResponse({"error": "No comments found"}, status=404)
    data["results"] = fix_mojibake(data["results"])
    return JsonResponse(data, safe=False, json_dumps_params={"ensure_ascii": False})

#approve comments
@csrf_exempt
@jwt_required
def approve_comments(request, comment_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE cmd2 SET status = 1 WHERE id = %s", [comment_id])
    return JsonResponse(
        {
            "success": True,
            "message": f"Comment {comment_id} approved",
            "comment_id": comment_id,
            "status": 1,
        }
    )

# unapprove comments
@csrf_exempt
@jwt_required
def unapprove_comments(request, comment_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE cmd2 SET status = 2 WHERE id = %s", [comment_id])
    return JsonResponse(
        {
            "success": True,
            "message": f"Comment {comment_id} unapproved",
            "comment_id": comment_id,
            "status": 2,
        }
    )

#block ip address
@csrf_exempt
@jwt_required
def block_ip_from_comment(request, comment_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Fetch IP from cmd2 table
    with connection.cursor() as cursor:
        cursor.execute("SELECT ip_address FROM cmd2 WHERE id = %s", [comment_id])
        row = cursor.fetchone()
        if not row or not row[0]:
            return JsonResponse({"error": "IP address not found for this comment"}, status=404)
        ip = row[0]

    ip_date = now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert into ip_address table
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO `ip_address` (`blocked-ip`, `ip_date`) VALUES (%s, %s)",
            [ip, ip_date]
        )

    return JsonResponse({
        "success": True,
        "message": f"IP {ip} blocked successfully",
        "blocked_ip": ip,
        "date": ip_date
    })

# delete comment
@jwt_required
def delete_comments(request, comment_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM cmd2 WHERE id = %s", [comment_id])
    return JsonResponse(
        {
            "success": True,
            "message": f"Comment {comment_id} deleted",
            "comment_id": comment_id,
        }
    )


# -------- Blocked IPs --------
# ip address view
@jwt_required
def get_blocked_ips_views(request):
    data = get_blocked_ips(request)
    if not data["results"]:
        return JsonResponse({"error": "No blocked IP addresses found"}, status=404)
    return JsonResponse(data, safe=False, json_dumps_params={"ensure_ascii": False})

# unblock IP address
@csrf_exempt
@jwt_required
def unblock_ip_views(request, ip_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM `ip_address` WHERE id = %s", [ip_id])
    return JsonResponse(
        {
        "success": True, 
        "message": f"IP with id {ip_id} unblocked successfully",
        "ip_address_id": ip_id
        }
    )
    
@csrf_exempt
@jwt_required
def search_with_ipaddress(request):
    if request.method != "GET":  # Use GET to easily test in browser or Postman
        return JsonResponse({"error": "Only GET method is allowed"}, status=405)

    search_ip = request.GET.get("blocked_ip")  # ?blocked_ip=1.2.3.4
    if not search_ip:
        return JsonResponse({"error": "IP is required"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, `blocked-ip` AS blocked_ip, ip_date FROM ip_address WHERE `blocked-ip` = %s",
            [search_ip]
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]

    return JsonResponse({
        "code": 200,
        "message": "Fetch Successfully",
        "results": results
    })
    
@csrf_exempt
@jwt_required
def search_and_block(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)
    
    search_ip = request.POST.get("blocked_ip")  # Reading from POST
    if not search_ip:
        return JsonResponse({"error": "IP is required"}, status=400)

    with connection.cursor() as cursor:
        # 1. Check if IP exists in cmd2
        cursor.execute("SELECT id, ip_address FROM cmd2 WHERE ip_address = %s", [search_ip])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({"message": "IP not found"}, status=404)

        # 2. Check if already blocked
        cursor.execute("SELECT id FROM ip_address WHERE `blocked-ip` = %s", [search_ip])
        already_blocked = cursor.fetchone()
        if already_blocked:
            return JsonResponse({"message": "IP already blocked"}, status=200)

        # 3. Insert into ip_address
        ip_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO ip_address (`blocked-ip`, ip_date) VALUES (%s, %s)",
            [search_ip, ip_date]
        )

    return JsonResponse({
        "message": "IP blocked successfully",
        "blocked_ip": search_ip,
        "blocked_at": ip_date
    })
    
# -------------home page details----------------
# count the total number of articles
@jwt_required
def total_news_count(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM newsmalayalam")
        total = cursor.fetchone()[0]
    return JsonResponse({
        "status": 200,
        "message": "Total news count fetched successfully",
        "total_news": total
    })

# last updated by
@jwt_required
def get_last_update(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                n.id, 
                n.newsHde, 
                a.Username AS editor,
                n.date,
                DATEDIFF(CURDATE(), n.date) AS days_since_update
            FROM newsmalayalam n
            LEFT JOIN admin1 a ON n.status_mge = a.AdminId
            WHERE status_cur = 0 AND n.date IS NOT NULL
            ORDER BY n.date DESC, n.id DESC
            LIMIT 1;
        """)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]

    results = fix_mojibake(results)

    return JsonResponse({
        "code": 200,
        "message": "Last updated by news fetched successfully",
        "results": results
    })
    
# todays updates
@jwt_required
def updates_today_view(request):
    today = date.today().strftime("%Y-%m-%d")  # Gets current date as "2025-08-05"  
    with connection.cursor() as cursor:
    # Query to get today's news with admin info
        query = """
           SELECT 
            n.id,  
            n.date, 
            a.Username AS editor
            FROM newsmalayalam n
            LEFT JOIN admin1 a ON n.status_mge = a.AdminId
            WHERE n.status_cur = 0
            AND n.date IS NOT NULL
            AND DATE(n.date) = %s
            ORDER BY n.date DESC;
        """
        cursor.execute(query, [today]) 
            # Format results
        rows = cursor.fetchall()
        if rows:
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        else:
            results = []
                
    return JsonResponse({
        "code": 200,
        "message": f"Today's news updates ({today})",
        "query_date": today,
        "count": len(results),
        "results": results,
      
    })