from django.urls import path
from . import views

app_name = "focusai"


urlpatterns = [
    path('', views.landing_page, name="home"),
    path("timer", views.timer, name="timer"),
    path("summarization", views.summarization, name="summarization"),
    path("to-do", views.to_do, name="to-do"),
    path("stats", views.stats, name="stats"),
    path("api/start/", views.start_timer, name="start_timer"),
    path("api/pause/", views.pause_timer, name="pause_timer"),
    path("api/stop/", views.stop_timer, name="stop_timer"),
    path("api/phone_detected/", views.phone_detected, name="phone_detected"),
    path("api/resume/", views.resume_timer, name="resume_timer"),
    path('api/detection-status/', views.get_detection_status, name='detection_status'),
    path('api/tasks/add/', views.add_task, name='add_task'),
    path('api/tasks/<int:task_id>/toggle/', views.toggle_task, name='toggle_task'),
    path('api/tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('api/tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('api/tasks/delete-completed/', views.delete_completed_tasks, name='delete_completed_tasks'),
    path('api/summarize/', views.summarize_text_api, name='summarize_text_api'),
    path('contact', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path("api/get_or_create_user/", views.get_or_create_user, name="get_or_create_user"),
    path("get_tasks", views.get_tasks, name="get_tasks"),
    path("settings", views.settings, name="settings")

]