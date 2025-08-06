from django.http import JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import traceback

class JsonErrorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if settings.DEBUG:
            # Show detailed error in development
            return JsonResponse({
                "error": str(exception),
                "type": type(exception).__name__,
                "trace": traceback.format_exc()
            }, status=500)
        # Hide details in production
        return JsonResponse({"error": "Internal server error"}, status=500)

    def process_response(self, request, response):
        if response.status_code == 404 and not isinstance(response, JsonResponse):
            return JsonResponse({"error": "Invalid endpoint or resource not found"}, status=404)
        if response.status_code == 405 and not isinstance(response, JsonResponse):
            return JsonResponse({"error": "Method not allowed"}, status=405)
        return response
