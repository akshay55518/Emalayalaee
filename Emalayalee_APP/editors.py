from django.views.decorators.csrf import csrf_exempt
from .db_access import *
from .login_authetication import jwt_required
from django.http import JsonResponse
import json
from .views import get_paginated_list, get_record_by_id_view

# # ------------------Editor-----------------------
# #get all editors
@jwt_required
def get_editors(request):
    return get_paginated_list(request, "admin1", order_by="AdminId")


# add editor
@csrf_exempt
@jwt_required
def add_editor_views(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # Support both JSON body and query params
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST or request.GET  # Fallback to form/query params

        username = data.get("username")
        password = data.get("password")
        admin_type = data.get("adminType")

        if not username or not password or not admin_type:
            return JsonResponse({"error": "All fields are required"}, status=400)

        if int(admin_type) not in [1, 2, 3, 4]:
            return JsonResponse({"error": "Invalid adminType"}, status=400)

        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO admin1 (Username, Password, adminType, date, updDate)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [username, password, admin_type, date_now, date_now],
            )

        return JsonResponse({
            "message": "Editor added successfully",
            "editor": {
                "username": username,
                "adminType": admin_type,
                "created_at": date_now
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
# edit writer
@csrf_exempt
@jwt_required
def edit_editor_views(request, editor_id):
    if request.method == "GET":
        # Fetch editor details
        with connection.cursor() as cursor:
            cursor.execute("SELECT AdminId, Username, adminType, date, updDate FROM admin1 WHERE AdminId=%s", [editor_id])
            row = cursor.fetchone()
            if not row:
                return JsonResponse({"error": "Editor not found"}, status=404)
            columns = [col[0] for col in cursor.description]
            return JsonResponse(dict(zip(columns, row)))

    elif request.method == "POST":
        # Update editor
        username = request.POST.get("username")
        password = request.POST.get("password")
        admin_type = request.POST.get("adminType")

        if not (username or password or admin_type):
            return JsonResponse({"error": "No fields to update"}, status=400)

        updates, values = [], []
        if username:
            updates.append("Username=%s")
            values.append(username)
        if password:
            updates.append("Password=%s")
            values.append(password)
        if admin_type:
            updates.append("adminType=%s")
            values.append(admin_type)

        updates.append("updDate=%s")
        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        values.append(editor_id)

        try:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE admin1 SET {', '.join(updates)} WHERE AdminId=%s", values)
            return JsonResponse({"message": "Editor updated successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
# delete editor
@jwt_required
def delete_editor_views(request, editor_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)


    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM admin1 WHERE AdminId = %s", [editor_id])
        if cursor.rowcount == 0:
            return JsonResponse({"error": "Editor not found"}, status=404)
    return JsonResponse({
        "message": "Editor deleted successfully",
        "editor_id": editor_id})