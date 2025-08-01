import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from functools import wraps

class Login(APIView):
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

def jwt_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"detail": "Authorization header missing or malformed"}, status=401)

        token = auth_header.split(' ')[1].strip()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except ExpiredSignatureError:
            return JsonResponse({"detail": "Token has expired"}, status=401)
        except InvalidTokenError:
            return JsonResponse({"detail": "Invalid token"}, status=401)

        user_id = payload.get('user_id')
        if not user_id:
            return JsonResponse({"detail": "Invalid token payload"}, status=401)

        # Attach user_id to the request so views can access it
        request.user_id = user_id
        return view_func(request, *args, **kwargs)

    return wrapped_view