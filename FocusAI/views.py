from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from portal.models import FocusStats, Tasks, Profile
from django.utils import timezone
from .pytorch_cv_detect import phone_detector
import os
import json
import time
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .utils import summarize_text, get_weekly_breakdown, reset_if_needed, extract_doc, extract_pdf
from dotenv import load_dotenv
from supabase import Client, create_client
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseRedirect


active_timers = {}

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(url, key)


def login_required(view_func):
    """Custom decorator to require Supabase auth before accessing a page."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return HttpResponseRedirect('/focusai/login/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def landing_page(request):
    
    username = request.session.get("username")
    print(f"landing page, got the username: {username}")
    if username:
        return render(request, "landing.html", {"username" : username})
    else:
        return render(request, "landing.html", {})


@login_required
def timer(request):
    print("Got the GET for timer")
    return render(request, "timer.html", {})

@login_required
def summarization(request):
    return render(request, "summarization.html", {})


def contact(request):
    return render(request, "contact.html", {})


@csrf_exempt
@require_http_methods(["POST"])
def summarize_text_api(request):

    try:
        text = " "
        content = request.POST.get("text", None)
        if content:
            text += content + "\n"

        file = request.FILES.get("uploaded_file", None)


        if file:
            filename, file_extension = os.path.splitext(file.name)
            if file_extension == ".pdf":

                text += "\n" + extract_pdf(file) + "\n"

            elif file_extension == ".docx":
                text += "\n" + extract_doc(file) + "\n"



        if len(text) < 100:
            return JsonResponse({'error': 'Text must be at least 100 characters long'}, status=400)

        if len(text) > 50000:
            return JsonResponse({'error': 'Text is too long. Maximum 50,000 characters allowed'}, status=400)


        try:
            summary = summarize_text(text)


            return JsonResponse({
                'success': True,
                'summary': summary,
                'original_length': len(text),
                'summary_length': len(summary),
                'compression_ratio': round((1 - len(summary) / len(text)) * 100, 1)
            })

        except Exception as e:
            print(f"An error occured: {e}")
            return JsonResponse({
                'error': str(e)
            }, status=503)

    except json.JSONDecodeError:
        print("INVALID JSON FORMATTT")
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        print(f"ERRRORRRRR: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)



@login_required
def stats(request):
    stats, user_id = get_or_create_user(request)

    reset_if_needed(stats)

    context = get_weekly_breakdown(stats)

    response = render(request, "stats.html", context)
    response.set_cookie("user_id", user_id, max_age=60 * 60 * 24 * 365)
    return response


def get_or_create_user(request):

    user_id = request.session.get('user_id')
    if not user_id:
        return None, None
    else:
        try:
            stats = FocusStats.objects.get(user_id=user_id)
        except FocusStats.DoesNotExist:
            stats = FocusStats.objects.create(user_id=user_id)
    return stats, user_id


    

def start_timer(request):

    try:

        stats, user_id = get_or_create_user(request)
        

        reset_if_needed(stats)

        active_timers[user_id] = {
            'start_time': timezone.now(),
            'paused_time': None,
            'total_paused': 0,
            'stats': stats
        }

        detection_started = False
        if phone_detector.model is not None:
            print("Model has been loaded and we are calcing the detection started var")
            detection_started = phone_detector.start_detection(user_id)

        
        response = JsonResponse({
            "status": "started",
            "user_id": user_id,
            "phone_detection": detection_started,
            "message": "Timer started successfully"
        })
        response.set_cookie("user_id", user_id, max_age=60*60*24*365)

    except Exception as e:
        print(e)


    return response


def pause_timer(request):

    stats, user_id = get_or_create_user(request)
    
    if user_id in active_timers:
        active_timers[user_id]['paused_time'] = timezone.now()
        phone_detector.stop_detection()
        return JsonResponse({"status": "paused"})
    
    return JsonResponse({"status": "error", "message": "No active timer"})

def resume_timer(request):

    stats, user_id = get_or_create_user(request)
    
    if user_id in active_timers and active_timers[user_id]['paused_time']:
        pause_duration = (timezone.now() - active_timers[user_id]['paused_time']).total_seconds()
        active_timers[user_id]['total_paused'] += pause_duration
        active_timers[user_id]['paused_time'] = None
        

        detection_restarted = False
        if phone_detector.model is not None:
            detection_restarted = phone_detector.start_detection(user_id)
        
        return JsonResponse({
            "status": "resumed",
            "phone_detection": detection_restarted
        })
    
    return JsonResponse({"status": "error", "message": "No paused timer"})

def stop_timer(request):

    stats, user_id = get_or_create_user(request)
    

    phone_detector.stop_detection()
    
    if user_id not in active_timers:
        return JsonResponse({"status": "error", "message": "No active timer"})
    
    timer_data = active_timers[user_id]

    end_time = timezone.now()
    total_duration = (end_time - timer_data['start_time']).total_seconds()
    

    if timer_data['paused_time']:

        pause_duration = (end_time - timer_data['paused_time']).total_seconds()
        timer_data['total_paused'] += pause_duration
    

    duration = total_duration - timer_data['total_paused']
    duration = max(0, duration)

    stats.total_focus_time_day += duration
    stats.total_focus_time_week += duration
    stats.total_sesh_day += 1
    stats.total_sesh_week += 1
    stats.save()

    

    del active_timers[user_id]
    
    return JsonResponse({
        "status": "stopped",
        "duration": round(duration),
        "duration_hours": round(duration / 60, 1),
        "stats": {
            "sessions_today": stats.total_sesh_day,
            "focus_time_today": round(stats.total_focus_time_day),
            "focus_time_hours": round(stats.total_focus_time_day / 3600, 2),
            "phone_interruptions_today": stats.times_phone_stopped_day
        }
    })

@csrf_exempt
def phone_detected(request):

    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    detection_user_id = request.session.get("user_id")
    
    if not detection_user_id:
        return JsonResponse({"error": "No active user"}, status=400)
    
    try:
        stats = FocusStats.objects.get(user_id=detection_user_id)

    except FocusStats.DoesNotExist:

        return JsonResponse({"error": "User stats not found"}, status=404)
    

    reset_if_needed(stats)
    

    stats.times_phone_stopped_day += 1
    stats.times_phone_stopped_week += 1
    stats.save()


    return JsonResponse({
        "status": "phone_detected",
        "user_id": detection_user_id,
        "interruptions_today": stats.times_phone_stopped_day,
        "interruptions_week": stats.times_phone_stopped_week
    })

def get_detection_status(request):

    print("Inside the function")
    stats, user_id = get_or_create_user(request)
    
    print("Got the stats and user id")
    elapsed = time.time() - phone_detector.start_time if hasattr(phone_detector, 'start_time') else 1
    frame_rate = phone_detector.frame_count / elapsed if hasattr(phone_detector, 'frame_count') and elapsed > 0 else 0

    phone_detector_response = phone_detector.get_detection_stats()

    print("GOT THE DETECTION STATS FROM THE OBJECT")
    avg_conf = phone_detector_response["avg_recent_confidence"]

    high_conf_count = phone_detector_response["high_confidence_count"]


    should_pause, debug_info = phone_detector.should_trigger_detection()
    
    
    response_data = {
        "detection_running": phone_detector.is_running,
        "model_loaded": phone_detector.model is not None,
        "current_user": phone_detector.user_id,
        "timer_active": user_id in active_timers,
        "confidence": {
            "phone": getattr(phone_detector, 'current_confidence', 0),
            "avg_conf" : avg_conf,
            "high_conf_count" : high_conf_count
        },
        "frame_rate": round(frame_rate, 1),
        "last_detection": "Just now" if getattr(phone_detector, 'last_detection_time', 0) > time.time() - 5 else "None",
        "stats": {
            "interruptions_today": stats.times_phone_stopped_day,
            "sessions_today": stats.total_sesh_day,
            "focus_time_today": round(stats.total_focus_time_day),
            "focus_time_hours": round(stats.total_focus_time_day / 3600, 2)
        },
        "should_pause" : should_pause
    }

    print(f"""---------- THE RESPONSE OBJECT IS -------------
            {response_data}""")


    return JsonResponse(response_data)




@login_required
def to_do(request):
    
    user_id = request.session['user_id']
    tasks = Tasks.objects.filter(user_id=user_id).order_by('-created_at')
    
    return render(request, "to-do.html", {'tasks': tasks})

@csrf_exempt
@require_http_methods(["POST"])
def add_task(request):

    try:
        data = json.loads(request.body)
        task_text = data.get('task', '').strip()
        
        if not task_text:
            return JsonResponse({'error': 'Task cannot be empty'}, status=400)

        
        user_id = request.session['user_id']
        
        task = Tasks.objects.create(
            user_id=user_id,
            task=task_text
        )
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'task': task.task,
                'completed': task.completed,
                'created_at': task.created_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def toggle_task(request, task_id):

    try:
        if 'user_id' not in request.session:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        user_id = request.session['user_id']
        task = get_object_or_404(Tasks, id=task_id, user_id=user_id)
        
        task.completed = not task.completed
        task.save()
        
        return JsonResponse({
            'success': True,
            'completed': task.completed
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def edit_task(request, task_id):

    try:
        data = json.loads(request.body)
        new_task_text = data.get('task', '').strip()
        
        if not new_task_text:
            return JsonResponse({'error': 'Task cannot be empty'}, status=400)

        
        user_id = request.session['user_id']
        task = get_object_or_404(Tasks, id=task_id, user_id=user_id)
        
        task.task = new_task_text
        task.save()
        
        return JsonResponse({
            'success': True,
            'task': task.task
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_task(request, task_id):

    try:
        user_id = request.session['user_id']
        task = get_object_or_404(Tasks, id=task_id, user_id=user_id)
        
        task.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_completed_tasks(request):

    try:
        user_id = request.session['user_id']

        completed_tasks = Tasks.objects.filter(user_id=user_id, completed=True)
        count = completed_tasks.count()
        
        if count == 0:
            return JsonResponse({'message': 'No completed tasks to delete', 'count': 0})

        completed_tasks.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Deleted {count} completed task{"s" if count != 1 else ""}',
            'count': count
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
def get_tasks(request):

    if request.method == "GET":

        tasks = len(Tasks.objects.filter(user_id=request.session.get("user_id"), completed=False))

        print(f"Amount of unchecked tasks: {tasks}")

        return JsonResponse({'amount' : int(tasks)}, status=200)


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

            return redirect("focusai:home")

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

            return redirect("focusai:home")

    else:
        return render(request, "signup.html", {})


def logout_view(request):
    request.session.flush()
    supabase.auth.sign_out()
    return redirect("focusai:home")
