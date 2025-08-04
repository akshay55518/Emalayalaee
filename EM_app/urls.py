from django.urls import path

from EM_app import Login
from EM_app.views import *



urlpatterns = [

    # Analytics
    path('activities/', activity_list, name='activity-list'),
    path('event_occurrences/',event_occurrence_view, name='events'),
    path('events/',page_views_chart_data, name='eventsPerDay'),
    path('session/', session_view, name='session'),
    path('active_users/',get_active_users, name='users_active'),




    # Editors

    path('admins/', admin_list_view, name='admin-list'),
    path('admins/<int:admin_id>/delete/', delete_admin_view, name='admin-delete'),
    path('admins/<int:admin_id>/edit/', update_admin_view, name='admin-update'),
    path('admins/create/', create_admin_view, name='admin-create'),
    path('admins/<int:admin_id>/', get_editor_view, name='get-editor'),
    path('admin/roles/', get_roles, name='get_roles'),

  










]

