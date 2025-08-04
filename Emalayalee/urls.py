from django.contrib import admin
from django.urls import path, include
from advertisement.views import *

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("Emalayalee_APP.urls")),
    
    path("advt/", include("advertisement.urls")),
    # count information displayed in the home part
    path("home/", home_count_view, name="home"),
    # articles published today
    path("articles_today/", articles_today, name="todays_articles"),
]
