from django.http import JsonResponse
from django.views import View
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunRealtimeReportRequest, Dimension, Metric, DateRange, RunReportRequest
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ActiveUsersView(View):
    """Replicates the 'Active Users in Last 30 Minutes' dashboard"""

    def get(self, request):
        try:
            client = BetaAnalyticsDataClient.from_service_account_file(
                settings.GOOGLE_ANALYTICS_KEY_FILE
            )

            response = client.run_realtime_report(
                RunRealtimeReportRequest(
                    property=f"properties/{settings.GOOGLE_ANALYTICS_PROPERTY_ID}",
                    dimensions=[Dimension(name="country")],
                    metrics=[Metric(name="activeUsers")],
                )
            )

            total_active = 0
            countries = []

            for row in response.rows:
                country = row.dimension_values[0].value or "Unknown"
                users = int(row.metric_values[0].value)
                countries.append({"country": country, "active_users": users})
                total_active += users

            countries_sorted = sorted(countries, key=lambda x: x["active_users"], reverse=True)
            active_per_minute = round(total_active / 30, 1) if total_active > 0 else 0

            return JsonResponse({
                "active_users_last_30_min": total_active,
                "active_users_per_minute": active_per_minute,
                "countries": countries_sorted,
                "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "view_realtime_link": f"https://analytics.google.com/analytics/web/#/realtime/overview/{settings.GOOGLE_ANALYTICS_PROPERTY_ID}",
            })
        except Exception as e:
            logger.error(f"Realtime API Error: {str(e)}")
            return JsonResponse({
                "status": "error",
                "message": str(e),
                "solution": "Check your GA4 property ID and service account permissions",
            }, status=500)


class BasicMetricsView(View):
    """Simplified GA4 analytics endpoint for active users & page views"""

    def get(self, request):
        try:
            client = BetaAnalyticsDataClient.from_service_account_file(
                settings.GOOGLE_ANALYTICS_KEY_FILE
            )
            response = client.run_report(
                RunReportRequest(
                    property=f"properties/{settings.GOOGLE_ANALYTICS_PROPERTY_ID}",
                    dimensions=[Dimension(name="date")],
                    metrics=[Metric(name="activeUsers"), Metric(name="screenPageViews")],
                    date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
                )
            )

            return JsonResponse({
                "active_users": sum(int(row.metric_values[0].value) for row in response.rows),
                "page_views": sum(int(row.metric_values[1].value) for row in response.rows),
                "daily_breakdown": [
                    {
                        "date": row.dimension_values[0].value,
                        # "active_users": row.metric_values[0].value,
                        "page_views": row.metric_values[1].value,
                    } for row in response.rows
                ],
            })
        except Exception as e:
            logger.error(f"GA4 Error: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
            
class EventMetricsView(View):
    """Get event counts and key events"""

    def get(self, request):
        try:
            client = BetaAnalyticsDataClient.from_service_account_file(
                settings.GOOGLE_ANALYTICS_KEY_FILE
            )
            response = client.run_report(
                RunReportRequest(
                    property=f"properties/{settings.GOOGLE_ANALYTICS_PROPERTY_ID}",
                    dimensions=[Dimension(name="eventName")],
                    metrics=[Metric(name="eventCount")],
                    date_ranges=[DateRange(start_date="1daysAgo", end_date="today")],
                )
            )

            return JsonResponse({
                "total_events": sum(int(row.metric_values[0].value) for row in response.rows),
                "events_by_name": [
                    {
                        "event_name": row.dimension_values[0].value,
                        "count": row.metric_values[0].value,
                    } for row in response.rows
                ],
            })
        except Exception as e:
            logger.error(f"Event Metrics Error: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
def get_sessions_historical(request, days=7):
    """Get session counts for specified time period"""
    try:
        days_int = int(days) if str(days).isdigit() else 1
        if days_int < 0:
            days_int = 1

        client = BetaAnalyticsDataClient.from_service_account_file(
            settings.GOOGLE_ANALYTICS_KEY_FILE
        )

        response = client.run_report(
            RunReportRequest(
                property=f"properties/{settings.GOOGLE_ANALYTICS_PROPERTY_ID}",
                dimensions=[Dimension(name="date")],
                metrics=[Metric(name="sessions")],
                date_ranges=[DateRange(start_date=f"{days_int}daysAgo", end_date="today")],
            )
        )

        return JsonResponse({
            "total_sessions": sum(int(row.metric_values[0].value) for row in response.rows),
            "daily_breakdown": [
                {
                    "date": row.dimension_values[0].value,
                    "sessions": int(row.metric_values[0].value),
                } for row in response.rows
            ],
            "time_period": f"Last {days_int} days",
        })
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        return JsonResponse({
            "error": "Failed to fetch session data",
            "details": str(e),
            "solution": "Ensure days parameter is a positive integer",
        }, status=400)