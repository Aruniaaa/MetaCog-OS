from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .utils import process, return_prompt, get_quiz, return_valid_quiz, store_in_vdb, agent
from supabase import Client, create_client
import os
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from portal.models import Profile, Quizzes, WrongQuestions
from dotenv import load_dotenv
from functools import wraps
from markdown_it import MarkdownIt
from mdit_py_plugins.texmath import texmath_plugin
from datetime import timedelta


load_dotenv()


url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(url, key)

def login_required(view_func):
    """Custom decorator to require Supabase auth before accessing a feature"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return HttpResponseRedirect('/saathi/login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view



def home(request):
    username = request.session.get("username")

    if username:
     return render(request, "home.html", {"username" : username})
    else:
        return render(request, "home.html", {})

@login_required
def chat(request):
    return render(request, "chat.html", {})

def contact(request):
    return render(request, "contacts.html", {})


@method_decorator(csrf_exempt, name='dispatch')
class ChatAPI(View):

    def post(self, request):

        try:


            data = json.loads(request.body)


            query = data.get('query', '').strip()


            if not query:
                return JsonResponse({
                    'error': 'No query provided'
                }, status=400)
            
            context = request.session.get("context", [])
           

            bot_response = process(query, context[-2: ])

            context.append({"user_message" : query, "bot_response" : bot_response})

            if len(context) > 2:

                context = context[-2: ]

            request.session["context"] = context

            md = MarkdownIt("commonmark").use(texmath_plugin, "math").enable('table')
            bot_response = md.render(bot_response)

            return JsonResponse({
                'response': bot_response,
                'status': 'success'
            })

        except json.JSONDecodeError as e:
            return JsonResponse({
                'error': 'Invalid JSON in request'
            }, status=400)

        except Exception as e:

            return JsonResponse({
                'error': 'An error occurred processing your request',
                'details': str(e),
                'type': type(e).__name__
            }, status=500)

@login_required
def quiz_gen(request):

    existing_quiz = request.session.get("quiz", None)
    
    if request.method == "GET":

        if existing_quiz is not None:
            return render(request, "quiz_gen.html", {"existing_quiz" : True})
        else:
            return render(request, "quiz_gen.html", {"existing_quiz": False})


    elif request.method == "POST" and existing_quiz is None:
        try:
            content = request.POST.get('content', None)
            file = request.FILES.get('uploaded_file', None)

            if not content and not file:
                return render(request, "quiz_gen.html", {"message" : "Both fields can not be empty! Please upload some content."})

            prompt = return_prompt(file, content)

            quiz = get_quiz(prompt)

            try:

                quiz_dict = json.loads(quiz)
                if "error" in quiz:
                    return render(request, "quiz_gen.html", {"message" : "Rate limit reached. Let's try again in a while?"})

                md = MarkdownIt().use(texmath_plugin)

                for i in range(len(quiz_dict)):
                    quiz_dict[i]['question'] = md.render(quiz_dict[i]['question'])

            except Exception as e:
                print(e)
                return render(request, "quiz_gen.html", {"message" : str(e)})


            request.session["quiz"] = quiz_dict

            return render(request, "quiz_gen.html", {
                "generated": True
            })
        except Exception as e:
                print(e)
                return render(request, "quiz_gen.html", {"message" : str(e)})

    elif existing_quiz is not None:
        return render(request, "quiz_gen.html", {
            "generated": True
        })


@login_required
def take_quiz(request):

    
    if request.method == "GET":
        quiz = request.session.get("quiz")
        if quiz:    
            return render(request, "take_quiz.html", {"questions" : quiz})
        else:
            return render(request, "quiz_404.html", {})



@login_required
def submit_quiz(request):

    if request.method == "POST":
        score = 0
        wrong_indices = []
        data_to_store = {}

        wrong_questions_list = []
        options = []
        answers = []

        quiz = request.session.get("quiz")
        questions = len(quiz)
        
        for i in range(questions):
            correct_letter = quiz[i]["answer"]
            correct_index = ord(correct_letter) - 65
            if correct_index + 1 == int(request.POST.get(f"question{i + 1}")):
                score += 1
            else:
                wrong_indices.append(i)

        
        user_id = request.session.get("user_id")
        profile, created = Profile.objects.get_or_create(
            supabase_id=user_id,
            defaults={'supabase_id': user_id}
        )

        new_quiz = Quizzes(user_id=profile, correct_count=score, total_questions=questions, accuracy=score / questions * 100)
        new_quiz.save()
        request.session.pop("quiz", None)

        username = request.session.get("username")

        if score != questions:

            wrong_questions = ""

            for index in wrong_indices:
                question = quiz[index]["question"]
                correct_letter = quiz[index]["answer"]
                correct_index = ord(correct_letter) - 65
                correct_option = quiz[index]["options"][correct_index]

                user_answer = quiz[index]["options"][int(request.POST.get(f"question{index + 1}")) - 1]

                wrong_questions_list.append(question)
                options.append(quiz[index]["options"])
                answers.append(correct_option)


                string = f"\nThe question was : {question} | User's answers was: {user_answer} | Correct answer was: {correct_option}\n"
                wrong_questions += string


            prompt = f"""Give me a clear explanation for each question I got wrong and help me understand the concept behind the correct answer. 
                Here are the questions I missed:

                {wrong_questions}

                Explain why the correct answer is right, what idea I misunderstood, and guide me to the correct reasoning without giving any extra unrelated info.""",

            store_in_vdb(wrong_questions, user_id)

            agent_prompt = f"""
            User ID: {user_id}

            Here are the questions the user got wrong:

            {wrong_questions}

            Your job:
            - Retrieve similar quizzes from this user's quiz history.
            - Identify common patterns.
            - Explain what topics they need to revise.
            - Give tips, suggestions, tricks, and feedback.
            """

            agent_response = agent.invoke({"messages": [agent_prompt]})
            agent_response = agent_response['messages'][-1].content

            md = MarkdownIt().use(texmath_plugin)
            agent_response = md.render(agent_response)


            data_to_store["questions"] = wrong_questions_list
            data_to_store["options"] = options
            data_to_store["answers"] = answers

            profile.wrong_questions_amt += len(wrong_questions_list)
            print(f"Before generating a quiz automatically, amount of wrong questions: {profile.wrong_questions_amt}\n\n")
            profile.save()

            new_data = WrongQuestions(
                user_id=user_id,
                quiz_id=new_quiz,
                wrong_questions_data=data_to_store
            )
            new_data.save()

            if profile.wrong_questions_amt >= 15:

                i = 1
                while len(data_to_store["questions"]) < 15:

                    print("Retreiving data from past wrong answers...\n\n")

                    more_data = WrongQuestions.objects.filter(user_id=user_id).exclude(id=new_data.id).select_related('quiz_id').order_by('-quiz_id__timestamp').first()

                    if not more_data:
                        print("No more past data available")
                        break

                    past_questions = more_data.wrong_questions_data["questions"]
                    past_options = more_data.wrong_questions_data["options"]
                    past_answers = more_data.wrong_questions_data["answers"]


                    for idx in range(len(past_questions)):
                        if len(data_to_store["questions"]) >= 15:
                            break


                        data_to_store["questions"].append(past_questions[idx])
                        data_to_store["options"].append(past_options[idx])
                        data_to_store["answers"].append(past_answers[idx])


                    if len(data_to_store["questions"]) >= 15:
                        break


                print(f"UPDATED DATA TO ASK QUESTIONS ON: {data_to_store}")

                valid_quiz = return_valid_quiz(data_to_store)
                request.session["quiz"] = valid_quiz
                profile.wrong_questions_amt = 0
                profile.save()
                print(f"Current amount of wrong questions: {profile.wrong_questions_amt}")

            return render(request, "quiz_submit.html", {"username" : username, "score" : score, "prompt": prompt, "total" : questions, "agent_feedback": agent_response})
        
        else:
            prompt = f"No prompt or feedback to see here! Congratulations for acing the test!<3"
            
            return render(request, "quiz_submit.html", {"username" : username, "score" : score, "prompt": prompt, "total" : questions})
        
                       



@login_required
def progress(request):
    
    if request.method == "GET":

        user_id = request.session.get("user_id")
        profile = Profile.objects.filter(supabase_id=user_id).first()
        total_quizzes_taken_30 = Quizzes.objects.filter(user_id=profile).order_by('-timestamp')[:30]
        total_quizzes_taken =  Quizzes.objects.filter(user_id=profile)
        total_questions_answered = 0
        accuracies = []
        streak = 0

        for quiz in total_quizzes_taken_30:

            total_questions_answered += quiz.total_questions
            accuracies.append(quiz.accuracy)

        i = 0

        while i < len(total_quizzes_taken) - 1 and (total_quizzes_taken[i].timestamp.date() - total_quizzes_taken[i + 1].timestamp.date()) == timedelta(days=1):
            streak += 1
            i+= 1

        improvement_percentage = 0
        if len(accuracies) >= 10:  

            first_5_avg = sum(accuracies[-5:]) / 5 
            last_5_avg = sum(accuracies[:5]) / 5    
            
            if first_5_avg > 0:  
                improvement_percentage = ((last_5_avg - first_5_avg) / first_5_avg) * 100
        
        avg_acc = sum(accuracies) / len(accuracies)  if accuracies else 0
        max_acc = max(accuracies) if accuracies else 0

        context = {
            'total_quizzes': len(total_quizzes_taken),
            'total_questions': total_questions_answered,
            'improvement': round(improvement_percentage, 1),
            'avg_acc': round(avg_acc, 1),
            'best_acc': round(max_acc, 1),
            'streak': streak,
            'accuracies': json.dumps(accuracies)  
        }


        return render(request, "progress.html", context)


@login_required
def progress(request):
    if request.method == "GET":

        user_id = request.session.get("user_id")
        profile = Profile.objects.filter(supabase_id=user_id).first()
        accuracies = [45, 52, 58, 63, 59, 55, 61, 68, 72, 69, 65, 70, 75, 78, 74, 71, 68, 72, 76, 80, 83, 81, 78, 82,
                      85, 87, 84, 86, 89, 91, 88]


        context = {
            'total_quizzes': 67,
            'total_questions': 140,
            'improvement': 29,
            'avg_acc': 78.92,
            'best_acc': 100,
            'streak': 76,
            'accuracies': json.dumps(accuracies)
        }

        return render(request, "progress.html", context)

def login(request):
    if request.method == "GET":
        return render(request, "login.html", {})
    elif request.method == "POST":
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
            return render(request, "login.html", {"message": str(e)})

        if response.user:
            user_id = response.user.id

            try:
                user = Profile.objects.get(supabase_id=user_id)
                username = user.username
            except Profile.DoesNotExist:
                username = email.split("@")[0]

            request.session["user_id"] = user_id
            request.session["username"] = username

            return redirect("saahti:home")



def signup(request):

    if request.method == "GET":
        return render(request, "signup.html", {})
    elif request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            response = supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password
                }
            )

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

                return redirect("saathi:home")
        except Exception as e:
            return render(request, "signup.html", {"message" : str(e)})

def logout_view(request):
    request.session.flush()
    supabase.auth.sign_out()
    return redirect("saathi:home")
