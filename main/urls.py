from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('login/', views.user_login, name="login"),
    path('signup/', views.signup, name="signup"),
    path('logout/', views.logout_view, name='logout'),

    path('story/', views.story, name="story"),
    path('fetch_stories/<int:source_id>/', views.fetch_stories, name='fetch_stories'),
    path('add_or_edit_story/', views.add_or_edit_story, name='add_or_edit_story'),
    path('delete_story/<int:story_id>/', views.delete_story, name='delete_story'),

    path('source/', views.source, name="source"),
    path('source/delete/<int:source_id>/', views.delete, name='delete'),
    path('add_or_edit_source/', views.add_or_edit_source, name='add_or_edit_source'),

    path('save_new_company/', views.save_new_company, name='save_new_company'),
]
