from django.urls import path, re_path
from .views import *

urlpatterns = [
    #advertisement corresponding to tye like HOMERIGHT..
    path('<str:type>/',advt_view, name='advt'),
    
     #edit advertisement 
    path('edit-adv/<int:id>', editing_ad, name='edit_ad'),

    #delete advertisement
    path('delete-adv/<int:id>/', delete_ad, name='delete_ad'),
    
    #create advertisement
    path('add-adv/<str:type>/', create_ad, name='create_ad'),

    #visitors viewing corresponding to advertisement id
    path('visitor/<int:id>/',visitors_view, name='visitor'),

    #view details from visitor table corresponding to ip address. used in search bar of visitor part
    re_path(r'^search/(?P<ip>(?:\d{1,3}\.){3}\d{1,3})/$',ip_based_search_view, name='view'),

]