from django.urls import path
from .views import *

urlpatterns = [
    # path('active-users/', Activeusers.as_view(), name='analytics'),
    # path('events/', SimpleGA4AnalyticsView.as_view(), name="events"),
    # path('sessions/', get_sessions_historical, name='sessions')
    path("active-users/", ActiveUsersView.as_view(), name="active_users"),
    path("page-views/", BasicMetricsView.as_view(), name="basic_metrics"),
    path("events/", EventMetricsView.as_view(), name="event_metrics"),
    path("sessions/", get_sessions_historical, name="sessions"),
]
