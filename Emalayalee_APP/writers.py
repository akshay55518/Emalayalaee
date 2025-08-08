from .db_access import *
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .login_authetication import jwt_required
from django.http import JsonResponse
from .views import get_paginated_list, get_record_by_id_view



# ------------Writers------------
#get writers
@jwt_required
def get_writers(request):
    return get_paginated_list(request, "writers", order_by="id")

# get writers by id
@jwt_required
def get_writers_by_id_views(request, id):
    return get_record_by_id_view(
        request,
        "writers",
        id,
        {
            "id": "id", 
            "name": "nme", 
            "status": "status", 
            "date": "date"
        },
    )
    
# add writer
@csrf_exempt
@jwt_required
def add_writer_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    nme = request.POST.get("nme")
    date = now().strftime("%Y-%m-%d %H:%M:%S")
    
    with connection.cursor() as cursor:
            cursor.execute("INSERT INTO writers (nme, date) VALUES (%s, %s)", [nme, date])
    return JsonResponse(
        {
            "success": True,
            "message": f"Writer '{nme}' added successfully",
            "writer_name": nme,
            "date": date
        },
        status=201,
    )
    
# edit writer
@csrf_exempt
@jwt_required
def edit_writer_view(request, writer_id):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM writers WHERE id = %s", [writer_id])
            row = cursor.fetchone()
            if not row:
                return JsonResponse({"error": "Writer not found"}, status=404)
            columns = [col[0] for col in cursor.description]
            writer_data = dict(zip(columns, row))
        return JsonResponse(writer_data, json_dumps_params={"ensure_ascii": False}, safe=False)
    
    elif request.method == "POST":
        nme = request.POST.get("nme")
        date = now().strftime("%Y-%m-%d %H:%M:%S")
        if not nme:
            return JsonResponse({"error": "Name is required"}, status=400)
        with connection.cursor() as cursor:
            cursor.execute("UPDATE writers SET nme = %s, date = %s WHERE id = %s", [nme, date, writer_id])
        return JsonResponse(
            {
                "success": True,
                "message": f"Writer with ID {writer_id} updated successfully",
                "writer_name": nme,
                "date": date
            }, status=200,
        )
    # Handle unsupported methods
    return JsonResponse({"error": "Method not allowed"}, status=405)

# delete writer
@csrf_exempt
@jwt_required
def delete_writer_view(request, writer_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM writers WHERE id = %s", [writer_id])
    return JsonResponse(
        {
            "success": True,
            "message": f"Writer with ID {writer_id} deleted successfully",
            "writer_id": writer_id,
        }
    )