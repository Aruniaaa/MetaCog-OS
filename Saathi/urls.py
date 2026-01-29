from django.urls import path
from . import views

app_name = "saathi"


urlpatterns = [
    path("", views.home, name="home"),
    path("chat", views.chat, name="chat"),
    path("contact", views.contact, name="contact"),
    path("api", views.ChatAPI.as_view(), name="api"),
    path("login", views.login, name="login"),
    path("signup", views.signup, name="signup"),
    path("logout", views.logout_view, name="logout"),
    path("quiz_gen", views.quiz_gen, name="quiz_gen"),
    path("progress", views.progress, name="progress"),
    path("take_quiz", views.take_quiz, name="take_quiz"),
    path("submit_quiz", views.submit_quiz, name="submit_quiz")
]