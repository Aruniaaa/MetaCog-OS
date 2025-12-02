from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("contact", views.contact, name="contact"),
    path("signup", views.signup_view, name="signup"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout")
]