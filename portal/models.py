from django.db import models
from django.utils import timezone


def get_current_date():
    """Helper function to get current date (not datetime)"""
    return timezone.now().date()


class FocusStats(models.Model):
    user_id = models.CharField(max_length=255, unique=True)

    total_sesh_day = models.IntegerField(default=0)
    total_focus_time_day = models.FloatField(default=0.0)
    times_phone_stopped_day = models.IntegerField(default=0)

    total_sesh_week = models.IntegerField(default=0)
    total_focus_time_week = models.FloatField(default=0.0)
    times_phone_stopped_week = models.IntegerField(default=0)

    last_day_reset = models.DateField(default=get_current_date)
    last_week_reset = models.DateField(default=get_current_date)

    def __str__(self):
        return f"{self.user_id}'s Focus Stats"


class Tasks(models.Model):
    user_id = models.CharField(max_length=255)

    task = models.CharField(max_length=50)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Task: {self.task} for {self.user_id}"


class Profile(models.Model):
    supabase_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    weekly_goal_hour = models.IntegerField(null=False, default=20)
    detect_phones = models.BooleanField(null=False, default=True)
    detect_tabs = models.BooleanField(null=False, default=True)

    last_report_generated = models.DateTimeField(default='1970-01-01 00:00:00')
    last_report_data = models.JSONField(null=True, blank=True)

    wrong_questions_amt = models.IntegerField(null=False, default=0)

    def __str__(self):
        return self.username



class Quizzes(models.Model):
    user_id = models.ForeignKey(Profile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    correct_count = models.IntegerField(null=False)
    total_questions = models.IntegerField(null=False)
    accuracy = models.FloatField(null=False)


class WrongQuestions(models.Model):
    user_id = models.CharField(max_length=255)
    quiz_id = models.ForeignKey(Quizzes, on_delete=models.CASCADE)
    wrong_questions_data =  models.JSONField(null=False)
