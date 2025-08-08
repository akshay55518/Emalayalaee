from .db_access import *
from django.views.decorators.csrf import csrf_exempt
from .login_authetication import jwt_required
from django.http import JsonResponse

# -------- Slider --------
# show slider data
@jwt_required
def get_slider_data_views(request):
    data = get_slider_data()
    if not data:
        return JsonResponse({"error": "No slider data found"}, status=404)
    return JsonResponse(data, safe=False)


# remove slider
@csrf_exempt
@jwt_required
def remove_from_slider_view(request, slider_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    remove_from_slider(slider_id)
    return JsonResponse(
        {"message": "Slider entry removed successfully", "slider_id": slider_id},
        status=200,
    )
    
    
# update slider
@csrf_exempt
@jwt_required
def update_slider_view(request, slider_id, news_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    success, message = update_slider_with_news(slider_id, news_id)
    return JsonResponse(
        {
            "success": success, 
            "message": message,
            "Slider position": slider_id+1,
            "News_ID": news_id
            }, status=200 if success else 400
    )
