from django.shortcuts import render, redirect
from supabase import Client, create_client
from dotenv import load_dotenv
import os
from .models import Profile


load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(url, key)


def home(request):

    username = request.session.get("username")

    if username:
        return render(request, "portal.html", {"username" : username})
    else:
        return render(request, "portal.html", {})


def contact(request):
    return render(request, "contact.html", {})



def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            response = supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password
                }
            )
        except Exception as e:
            print(e)
            return render(request, "login.html", {"message" : str(e)})


        if response.user:
            user_id = response.user.id


            try:
                user = Profile.objects.get(supabase_id=user_id)
                username = user.username
            except Profile.DoesNotExist:
                username = email.split("@")[0]


            request.session["user_id"] = user_id
            request.session["username"] = username
            print("LOGGED INNN")
            return redirect("portal:home")

    else:
        return render(request, "login.html", {})


def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        username = request.POST.get("username")

        try:
            response = supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password
                }
            )
        except Exception as e:
            print(e)
            return render(request, "signup.html", {"message" : str(e)})

        user = response.user
        if not user:
            return render(request, "signup.html", {"message": "Signup failed. Try again!"})

        if user:
            new_user = Profile.objects.create(
                supabase_id=user.id,
                username=username,
                email=email
            )
            new_user.save()

            request.session["user_id"] = user.id
            request.session["username"] = username
            print("SIGNED UPPPP")
            return redirect("portal:home")

    else:
        return render(request, "signup.html", {})


def logout_view(request):
    request.session.flush()
    supabase.auth.sign_out()
    return redirect("portal:home")
