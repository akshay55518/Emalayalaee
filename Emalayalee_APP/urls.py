from django.urls import path
from .login_authetication import *
from .views import *
from .obituaries import *
from .writers import *
from .slider import *
from .editors import *

urlpatterns = [

    path('api-login/', Login.as_view(), name="login"),
    
    # -------------------- NEWS --------------------
    # Get all news (paginated)
    path('news/', get_news, name='get_news'),
     # Get news by ID
    path('news/<str:news_id>/', get_news_by_id_views, name='get_news_by_id_views'),
    # Add news
    # path('add-news/', views.add_news_view, name='add_news'),
    path('add-news/<str:newsType>/', add_news_view, name='add_news'),
    # Edit news
    path('edit-news/<int:news_id>/', edit_news_view, name='edit_news'),
    # Search news by title
    path('search-news/<str:title>/', search_news_views, name='search_news_by_title'),

    # -------------------- NEWS TYPES --------------------
    # Get all news types
    path('newsTypes/', get_news_types_views, name='get_news_types'),
    # Get news by type
    path('news-types/<str:news_type>/', get_news_by_type_views, name='get_news_by_type'),
    # Get news by type & status (Published=0, Deleted=1, Draft=2, Scheduled=3)
    path('news-types-cur/<str:news_type>/<int:status_cur>/', get_news_by_type_and_status_views, name='get_news_by_type_and_status'),
    # Move news to other type
    path('move-news/<int:news_id>/<str:newsType>/', move_news_to_newsType_view, name='move_news_type'),
    # Copy news to other type (new ID, copyid set)
    path('copy-news/<int:news_id>/<str:newsType>/', copy_news_view, name='copy_news'),

    # -------------------- NEWS STATUS --------------------
    # Publish drafted news
    path('publish-news/<int:news_id>/', publish_news_view, name='publish_news'),
    # Soft delete news (move to trash)
    path('delete-news/<int:news_id>/', delete_news_view, name='delete_news'),
    # Restore deleted news
    path('restore-news/<int:news_id>/', restore_news_view, name='restore_news'),
    # Permanently delete news
    path('permanently-delete-news/<int:news_id>/', permanently_delete_news_view, name='permanently_delete_news'),

    # -------------------- SLIDER --------------------
    # Get all sliders
    path('slider/', get_slider_data_views, name='get_slider_data'),
    # Update slider with news
    path('update-slider/<int:slider_id>/<int:news_id>/', update_slider_view, name='add_slider_data'),
    # Remove news from slider
    path('remove-slider/<int:slider_id>/', remove_from_slider_view, name='remove_news_from_slider'),

    # -------------------- COMMENTS --------------------
    # Get all comments
    path('comments/', get_comments, name='get_comments'),
    # Get comments by ID
    path('comments/<int:id>/', get_comments_by_id_views, name='get_comments_by_id'),
    #show approved comments 1 for approved 2 for unapproved
    path('status-comments/<int:status>/', get_comments_by_status_views, name='get_comments_by_status'),
    # approved comments
    path('approve-comments/<int:comment_id>/', approve_comments, name='approve_comments'),
    # unapproved comments  
    path('comments/unapprove/<int:comment_id>/', unapprove_comments, name='unapprove_comments'),
    # delete comment
    path('delete-comments/<int:comment_id>/', delete_comments, name='delete_comments'),
    # block ip address from comment
    path('block-ip/<int:comment_id>/', block_ip_from_comment, name='block_ip_from_comment'),
    
    # -------------------IP address---------------------
    # ip address view
    path('blocked-ips/', get_blocked_ips_views, name='get_blocked_ips'),
    # upblock ip address
    path('unblock-ips/<int:ip_id>/', unblock_ip_views, name='unblock_ip_address'),
    # search ip_address
    path('search-ip/', search_with_ipaddress, name="search_with_ipaddress"),
    # search and block
    path('search-block/', search_and_block, name="search_and_block"),
    

    # -------------------- CHARAMAM --------------------
    # get all charamam
    path('obituaries/', get_charamam, name='get_charamam'),
    # get charamam with id
    path('obituaries/<int:id>/', get_charamam_by_id_views, name='get_charamam_by_id'),
    # add charamam 
    path('add-obituaries/', add_charamam_entry, name='add-obituaries'),
    # delete obituaries
    path('delete-obituaries/<int:id>/', delete_charamam_entry, name='delete-obituaries'),
    
    

    # -------------------- WRITERS --------------------
    # get all writers
    path('writers/', get_writers, name='get_writers'),
    # get writers with id
    path('writers/<int:id>/', get_writers_by_id_views, name='get_writers_by_id'),
    # add writers
    path('add-writer/', add_writer_view, name='add_writer'),
    # edit editors
    path('edit-writer/<int:writer_id>/', edit_writer_view, name='edit_writer'),
    # delete writer
    path('delete-writer/<int:writer_id>/', delete_writer_view, name='delete_writer'),

    # -------------------- SOCIAL MEDIA --------------------
    # Get today's post count
    path('count-social/', get_today_post_count, name='get_today_post_count'),
    # Mark post as posted in social media
    path('post-marked-social/<int:news_id>/<int:account_id>/', mark_as_posted_view, name='mark_as_posted'),
    
    # path('advertise/', views.advertise, name='advertise')
    
    # ------------------------editors-----------------------------
    # get all editors
    path('editors/', get_editors, name='get editor'),
    # add editors
    path('add-editor/', add_editor_views, name='add-editor'),
    # edit editors
    path('edit-editor/<int:editor_id>/', edit_editor_views, name='edit-editor'),
    # delete editors
    path('delete-editor/<int:editor_id>/', delete_editor_views, name='delete-editor'),
    
    # ------------------------Home page ----------------------------
    # total news count
    path('news-count/', total_news_count, name='news-count'),
    # news articles today
    path('updates-today/', updates_today_view, name='updates-today'),
    # last updated by
    path('last-updated/', get_last_update, name='last-updated'),
    
]
