from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .db_access import *
from .language_utils import fix_mojibake
from .login_authetication import jwt_required
from django.http import JsonResponse
import json
from .views import get_paginated_list, get_record_by_id_view

@jwt_required
def get_charamam(request):
    return get_paginated_list(request, "charamam", order_by="id")

@jwt_required
def get_charamam_by_id_views(request, id):
    return get_record_by_id_view(
        request,
        "charamam",
        id,
        {
            "id": "id",
            "name": "name",
            "date": "date",
            "news": "news",
            "images": "images2",
            "cdn": "cdn",
        },
    )

@jwt_required
@csrf_exempt
def add_charamam_entry(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name", "")
            news = data.get("news", "")
            dth = data.get("dth", "")
            language = data.get("language", "")
            images = data.get("images", "")
            images2 = data.get("images2", "")
            user_id = request.user_id

            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO charamam (name, news, dth, language, images, images2, date, status_cur, status_mge)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), 0, %s)
                """, [name, news, dth, language, images, images2, user_id])

            return JsonResponse({"message": "Charamam entry added successfully"})

        except Exception as e:
            return JsonResponse({"message": "Error", "error": str(e)}, status=500)

    return JsonResponse({"message": "Only POST method allowed"}, status=405)

@jwt_required
@csrf_exempt
def delete_charamam_entry(request, id):
    if request.method == "DELETE":
        try:
            user_id = request.user_id

            # Fetch data before deletion
            with connection.cursor() as cur:
                cur.execute("SELECT name FROM charamam WHERE id = %s AND status_cur = 0", [id])
                row = cur.fetchone()

                if not row:
                    return JsonResponse({"message": "Charamam entry not found or already deleted"}, status=404)

                name = row[0] or "CHARAMAM"

                # Mark as deleted
                cur.execute("""
                    UPDATE charamam
                    SET status_cur = 1, status_mge = %s
                    WHERE id = %s
                """, [user_id, id])

            # Add to resycle table
            move_to_resycle_table(
                newsid=id,
                mge=user_id,
                nswstype="CHARAMAM",
                db="charamam"
            )

            return JsonResponse({"message": "Charamam entry deleted successfully"})

        except Exception as e:
            return JsonResponse({"message": "Error", "error": str(e)}, status=500)

    return JsonResponse({"message": "Only DELETE method allowed"}, status=405)