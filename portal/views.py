from django.shortcuts import render, redirect
from supabase import Client, create_client
from dotenv import load_dotenv
import os
from .models import Profile, Quizzes, Tasks, FocusStats
from functools import wraps
from django.http import HttpResponseRedirect, JsonResponse
from cerebras.cloud.sdk import Cerebras
import json
from datetime import timedelta, datetime
from django.utils import timezone 


load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(url, key)


client = Cerebras(
        api_key=os.environ.get("CEREBRAS_API_KEY")
    )

report_schema = {
  "type": "object",
  "properties": {
    "Suggestions & Feedback": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "Tips & Trick": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "Recommended Resources": {
      "type": "array",
      "items": {
        "type": "string"
      },
    },
    "Pending Tasks & How to get them done": {
      "type": "array",
      "items": {
        "type": "string"
      },
    },
    "Suggested Priorities for Next Weeks": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "Suggestions & Feedback",
    "Tips & Trick",
    "Recommended Resources",
    "Suggested Priorities for Next Weeks"
  ]
}

def login_required(view_func):
    """Custom decorator to require Supabase auth before accessing a feature"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return HttpResponseRedirect('/portal/login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def home(request):

    username = request.session.get("username")

    if username:
        return render(request, "portal.html", {"username" : username})
    else:
        return render(request, "portal.html", {})


def contact(request):
    return render(request, "contact.html", {})


@login_required
def ai_suggestions(request):

    if request.method == "GET":

        user_id = request.session.get("user_id")

        stats = FocusStats.objects.get(user_id=user_id)
        profile = Profile.objects.filter(supabase_id=user_id).first()


        week_start = stats.last_week_reset

        weekly_quizzes = Quizzes.objects.filter(
            user_id=profile,
            timestamp__gte=week_start
        )


        total_questions_sum = sum(q.total_questions for q in weekly_quizzes)

        total_correct_sum = sum(q.correct_count for q in weekly_quizzes)
        

        overall_accuracy = 0.0
        if total_questions_sum > 0:
            overall_accuracy = (total_correct_sum / total_questions_sum) * 100

        context = {
            "total_focus": f"{stats.total_focus_time_week / 60:.1f}",
            "sessions": stats.total_sesh_week, 
            "avg_len": f"{stats.total_focus_time_week / stats.total_sesh_week:.1f}" if stats.total_sesh_week else 0, 
 
            "quizzes_comp": weekly_quizzes.count(), 
            "total_ques": total_questions_sum, 
            "overall_acc": f"{overall_accuracy:.1f}%",
            
        }

        return render(request, "ai_suggestions.html", context)
    
def make_report(request):
    
    user_id = request.session.get("user_id")


    user = Profile.objects.get(supabase_id=user_id)

    if user.last_report_generated is None or (timezone.now() - user.last_report_generated) > timedelta(days=7):


    
        stats = FocusStats.objects.filter(user_id=user_id).first()
        profile = Profile.objects.filter(supabase_id=user_id).first()

        weekly_goal_hour = user.weekly_goal_hour
        total_sesh_week = stats.total_sesh_week
        total_focus_time_week = stats.total_focus_time_week
        times_phone_stopped_week = stats.times_phone_stopped_week


        total_quizzes_taken_30 = Quizzes.objects.filter(user_id=profile).order_by('-timestamp')[:30]

        accuracies = [quiz.accuracy for quiz in total_quizzes_taken_30]

        uncomp_tasks = [task.task for task in Tasks.objects.filter(user_id=profile, completed=False)]


        prompt = f"""
            Analyze this user's study performance and provide a comprehensive report and actionable suggestions.

            Here is the user's data:
            - Weekly Goal Hour: {weekly_goal_hour}
            - Total Sessions This Week: {total_sesh_week}
            - Total Focus Time This Week (minutes): {total_focus_time_week}
            - Times Phone Interaction Stopped Focus This Week: {times_phone_stopped_week}
            - Last 30 Quiz Accuracies (0.0 to 1.0): {accuracies}
            - Uncompleted Tasks: {uncomp_tasks}

            The report should be structured into three main sections:
            1. **Analysis of Performance:** A summary of the user's performance against their goal, focus consistency, and recent knowledge retention (quiz accuracy). Identify key strengths and weaknesses.
            2. **Actionable Suggestions:** Provide 3-5 specific, clear, and actionable recommendations based on the analysis. These should cover areas like improving focus, optimizing study schedule, or addressing knowledge gaps identified in the quiz accuracies/uncompleted tasks.
            3. **Summary Statement:** A brief, encouraging, and summarizing conclusion.

            Maintain a professional, encouraging, and data-driven tone. Do not use any introductory or concluding filler text (e.g., "Here is your report," or "I hope this helps"). Present the analysis and suggestions directly.
            """


        completion = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": prompt},
        ],
        response_format={
            "type": "json_schema", 
            "json_schema": {
                "name": "report schema",
                "strict": True,
                "schema": report_schema
            }
        })

        report = json.loads(completion.choices[0].message.content)
  

        report_data = {
            "not_required": False,
            "report" : report
            
        }
        user.last_report_data = report_data
        user.last_report_generated = timezone.now()
        user.save()
    
        
        return JsonResponse(report_data)
    else:
  
        cached_data = user.last_report_data or {}
        cached_data["not_required"] = True
        return JsonResponse(cached_data)




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
