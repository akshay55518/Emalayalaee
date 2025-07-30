from django.urls import path
from . import views

urlpatterns = [
    # -------------------- NEWS --------------------
    # Get all news (paginated)
    path('news/', views.get_news, name='get_news'),
     # Get news by ID
    path('news/<str:news_id>/', views.get_news_by_id_views, name='get_news_by_id_views'),
    # Add news
    path('news/add/', views.add_news_view, name='add_news'),
    # Edit news
    path("news/edit/<int:news_id>/", views.edit_news_view, name="edit_news"),
    # Search news by title
    path('search/<str:title>/', views.search_news_by_title_views, name='search_news_by_title'),

    # -------------------- NEWS TYPES --------------------
    # Get all news types
    path('newsTypes/', views.get_news_types_views, name='get_news_types'),
    # Get news by type
    path('newsTypes/<str:news_type>/', views.get_news_by_type_views, name='get_news_by_type'),
    # Get news by type & status (Published=0, Deleted=1, Draft=2, Scheduled=3)
    path('newsTypes_cur/<str:news_type>/<int:status_cur>/', views.get_news_by_type_and_status_views, name='get_news_by_type_and_status'),
    # Move news to other type
    path('move/newsTypes/<int:news_id>/<str:newsType>/', views.move_news_to_newsType_view, name='move_news_type'),
    # Copy news to other type (new ID, copyid set)
    path('news/copy/<int:news_id>/<str:newsType>/', views.copy_news_view, name='copy_news'),

    # -------------------- NEWS STATUS --------------------
    # Publish drafted news
    path('news/publish/<int:news_id>/', views.publish_news_view, name='publish_news'),
    # Soft delete news (move to trash)
    path('news/delete/<int:news_id>/', views.delete_news_view, name='delete_news'),
    # Restore deleted news
    path('news/restore/<int:news_id>/', views.restore_news_view, name='restore_news'),
    # Permanently delete news
    path('news/permanently_delete/<int:news_id>/', views.permanently_delete_news_view, name='permanently_delete_news'),

    # -------------------- SLIDER --------------------
    # Get all sliders
    path('slider/', views.get_slider_data_views, name='get_slider_data'),
    # Update slider with news
    path('slider/update/<int:slider_id>/<int:news_id>/', views.update_slider_view, name='add_slider_data'),
    # Remove news from slider
    path('slider/remove/<int:slider_id>/', views.remove_from_slider_view, name='remove_news_from_slider'),

    # -------------------- COMMENTS --------------------
    # Get all comments
    path('comments/', views.get_comments, name='get_comments'),
    # Get comments by ID
    path('comments/<int:id>/', views.get_comments_by_id_views, name='get_comments_by_id'),
    #show approved comments 1 for approved 2 for unapproved
    path('comments/status/<int:status>/', views.get_comments_by_status_views, name='get_comments_by_status'),
    # approved comments
    path('comments/approve/<int:comment_id>/', views.approve_comments, name='approve_comments'),
    # unapproved comments  
    path('comments/unapprove/<int:comment_id>/', views.unapprove_comments, name='unapprove_comments'),
    # delete comment
    path('comments/delete/<int:comment_id>/', views.delete_comments, name='delete_comments'),
    # block ip address from comment
    path('comments/block-ip/<int:comment_id>/', views.block_ip_from_comment, name='block_ip_from_comment'),
    
    # -------------------IP address---------------------
    # ip address view
    path('blocked-ips/', views.get_blocked_ips_views, name='get_blocked_ips'),
    # upblock ip address
    path('unblock-ips/<int:ip_id>/', views.unblock_ip_views, name='unblock_ip_address'),
    

    # -------------------- CHARAMAM --------------------
    # get all charamam
    path('charamam/', views.get_charamam, name='get_charamam'),
    # get charamam with id
    path('charamam/<int:id>/', views.get_charamam_by_id_views, name='get_charamam_by_id'),

    # -------------------- WRITERS --------------------
    # get all writers
    path('writers/', views.get_writers, name='get_writers'),
    # get writers with id
    path('writers/<int:id>/', views.get_writers_by_id_views, name='get_writers_by_id'),
    # add writers
    path('writers/add/', views.add_writer_view, name='add_writer'),
    # edit editors
    path('writers/edit/<int:writer_id>', views.edit_writer_view, name='edit_writer'),
    # delete writer
    path('writers/delete/<int:writer_id>/', views.delete_writer_view, name='delete_writer'),

    # -------------------- SOCIAL MEDIA --------------------
    # Get today's post count
    path('social/count/', views.get_today_post_count, name='get_today_post_count'),
    # Mark post as posted in social media
    path('social/post_marked/<int:news_id>/<int:account_id>/', views.mark_as_posted_view, name='mark_as_posted'),
]
