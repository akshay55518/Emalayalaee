import json
import math
from collections import defaultdict
from advertisement.views import login_check

from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse


# Create your views here.
from .db_access import *
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.decorators import api_view
import logging

logger = logging.getLogger(__name__)
from django.utils import timezone
import geoip2.database
from django.conf import settings

def get_country_from_ip(ip_address):
    try:
        with geoip2.database.Reader(settings.GEOIP_PATH) as reader:
            response = reader.country(ip_address)
            return response.country.name
    except Exception:
        return "Unknown"


def get_active_users(request):
    try:
        # 1. Verify time calculation
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        logger.info(f"Querying IPs since {thirty_min_ago}")

        # 2. Enhanced query with debug info
        query = """
            SELECT * 
            FROM ip_address 
            WHERE ip_date >= %s
            ORDER BY ip_date DESC
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [thirty_min_ago])
            results = cursor.fetchall()
            logger.info(f"Found {len(results)} records in query")

            ip_addresses = [row[0] for row in results]
            logger.info(f"Sample IPs: {ip_addresses[:3]}")  # Log first 3 IPs

        # 3. Country detection with fallback
        country_counts = defaultdict(int)
        for ip in ip_addresses:
            try:
                country = get_country_from_ip(ip) or "Unknown"
                country_counts[country] += 1
            except Exception as e:
                logger.error(f"Error processing IP {ip}: {str(e)}")
                country_counts["Unknown"] += 1

        logger.info(f"Country distribution: {dict(country_counts)}")

        # 4. Return complete results
        return JsonResponse({
            'total_active': len(ip_addresses),
            'countries': [{"name": k, "count": v} for k, v in sorted(country_counts.items())],
            'query_time': thirty_min_ago.isoformat(),
            'status': 'success'
        })

    except Exception as e:
        logger.exception("Failed to get active users")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'debug': {
                'query_time': timezone.now().isoformat(),
                'thirty_min_ago': thirty_min_ago.isoformat() if 'thirty_min_ago' in locals() else None
            }
        }, status=500)


def activity_list(request):
    try:
        data = get_activity()
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'results': data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)





# Event occurrences

def event_occurrence_view(request):
    try:
        data = get_event_occurrences()

        return JsonResponse({
            "code": 200,
            "message": "Success",
            "data": data
        })
    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": "Error fetching event data",
            "error": str(e)
        }, status=500)


# Events per day

def page_views_chart_data(request):
    try:
        data = get_page_views_per_day()
        return JsonResponse({"code": 200, "data": data})
    except Exception as e:
        return JsonResponse({"code": 500, "error": str(e)}, status=500)



# session view

def session_view(request):
    """Return aggregated session metrics"""
    try:
        metrics = get_session_metrics()
        return JsonResponse({
            'status': 'success',
            'data': metrics
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def session_timeseries(request):
    """Return time-series session data"""
    try:
        # Get optional date filters from query params
        date_from = request.GET.get('from')
        date_to = request.GET.get('to')
        days = int(request.GET.get('days', 7))

        data = get_session_data(days=days, date_from=date_from, date_to=date_to)

        # Format dates to match your needs (YYYYMMDD in your screenshot)
        formatted_data = [
            {
                'date': item['session_date'].strftime('%Y%m%d'),
                'sessions': item['session_count'],
                'events': item['total_events']
            }
            for item in data
        ]

        return JsonResponse({
            'status': 'success',
            'data': formatted_data
        })

    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid date format or parameters'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)











# Editors ------------------------------------------------------------------------


# view for  editors page / admins




def admin_list_view(request):
    try:
        admins = get_all_admins()
        return JsonResponse({'status': 'success', 'admins': admins})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def delete_admin_view(request, admin_id):
    if request.method == 'DELETE':
        try:
            delete_admin_by_id(admin_id)
            return JsonResponse({'status': 'success', 'message': 'Admin deleted successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only DELETE method allowed'}, status=405)



@csrf_exempt
def update_admin_view(request, admin_id):
    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
            username = body.get('username')
            password = body.get('password')
            admin_type = body.get('adminType')

            if not all([username, password, admin_type]):
                return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)

            update_admin_by_id(admin_id, username, password, admin_type)
            return JsonResponse({'status': 'success', 'message': 'Admin updated successfully'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only PATCH method allowed'}, status=405)


@csrf_exempt
def create_admin_view(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            username = body.get('username')
            password = body.get('password')
            admin_type = body.get('adminType')

            if not all([username, password, admin_type]):
                return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)

            create_admin(username, password, admin_type)
            return JsonResponse({'status': 'success', 'message': 'Admin created successfully'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)



def get_editor_view(request, admin_id):
    try:
        editor = get_editor_by_id(admin_id)
        if editor:
            return JsonResponse({'status': 'success', 'editor': editor})
        else:
            return JsonResponse({'status': 'error', 'message': 'Editor not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        


# filter by roles
def get_roles(request):
    try:
        with connection.cursor() as cursor:
            # Fetch distinct adminType values and their counts from your admin1 table
            cursor.execute("""
                SELECT 
                    adminType as role_id,
                    COUNT(*) as count,
                    CASE adminType
                        WHEN 1 THEN 'Super Admin'
                        WHEN 2 THEN 'Chief Editor'
                        WHEN 3 THEN 'Editor'
                        ELSE 'Contributor'
                    END as role_name
                FROM admin1
                GROUP BY adminType
                ORDER BY adminType
            """)

            columns = [col[0] for col in cursor.description]
            roles = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return JsonResponse({'roles': roles})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





