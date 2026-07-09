import os
from datetime import timedelta

import fitz
from django.utils import timezone
from docx import Document
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError, ClientError
from markdown_it import MarkdownIt
from mdit_py_plugins.texmath import texmath_plugin

from portal.models import FocusStats, Profile

load_dotenv()


api_key = os.getenv("GEMINI_KEY")

client = genai.Client(api_key=api_key)


def extract_pdf(file):

    pdf_bytes = file.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    all_text = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text()
        text = " ".join(text.split())
        all_text.append(text)

    return "\n\n".join(all_text).strip()


def extract_doc(file):

    doc = Document(file)
    fullText = []

    for para in doc.paragraphs:
        fullText.append(para.text)

    return "\n".join(fullText)


def summarize_text(text):

    prompted_query = f"""
    Summarize the following text with a clean, structured, and highly readable markdown format.

    Requirements:
    - Start with a 1–2 sentence overview ONLY — no filler phrases like “Here’s a summary”.
    - Use clear markdown headings (##) and bullet points.
    - Add a blank line between every major section.
    - Preserve logical grouping from the original text.
    - Keep paragraphs short and avoid dense blocks of text.
    - Include proper whitespacing, especially between different sections and headings.

    Text to summarize:
    {text}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompted_query
        )

        summarized = response.text
        md = MarkdownIt("commonmark").use(texmath_plugin, "math").enable("table")
        bot_response = md.render(summarized)

        bot_response = f"""
        <div class="markdown-content">
            {bot_response}
        </div>
        """
        return bot_response

    except ClientError as e:
        if e.code == 429:
            return "## ❗❗ Rate limit reached\n\nPlease slow down and try again in a moment."
        else:
            return "## ⚠️ Something went wrong\n\nPlease try again later."

    except APIError:
        return "## ⚠️ API issue\n\nUnable to complete the request right now."

    except Exception:
        return "## ⚠️ Unexpected error\n\nAn unexpected error occurred. Please try again later."


def get_weekly_breakdown(stats):

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    daily_hours = [4, 5, 9, 1, 3.4, 6, 1.5]

    today = timezone.now().date()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)

    # for i, day in enumerate(days):
    #     current_day = monday + timedelta(days=i)

    #     if current_day == today:
    #         daily_hours.append(stats.total_focus_time_day / 3600)
    #     elif current_day < today:
    #         daily_hours.append(0)
    #     else:
    #         daily_hours.append(0)

    total_focus_hours = sum(daily_hours)
    daily_avg_hours = round(total_focus_hours / 7 if total_focus_hours > 0 else 0)

    user_id = stats.user_id

    user = Profile.objects.get(supabase_id=user_id)

    weekly_goal_hour = user.weekly_goal_hour
    goal_completion = (
        min(100, (total_focus_hours / weekly_goal_hour) * 100)
        if total_focus_hours > 0
        else 0
    )
    phoneInterruptions = stats.times_phone_stopped_week

    max_interruption_rate = 3

    focus_percentage = max(0, 100 - (phoneInterruptions / max_interruption_rate * 100))
    focus_percentage = round(focus_percentage, 2)
    focus_percentage = 59  # hardcoded value

    if total_focus_hours > 0 and daily_hours:
        max_hours = max(daily_hours)
        min_hours = min(daily_hours)

        best_day_index = daily_hours.index(max_hours)
        worst_day_index = daily_hours.index(min_hours)

        best_day = days[best_day_index]
        worst_day = days[worst_day_index]

        best_day_hours = max_hours
        worst_day_hours = min_hours
    else:
        best_day = worst_day = "N/A"
        best_day_hours = worst_day_hours = 0

    longest_session_hours = max(daily_hours)
    streak_days = sum(1 for m in daily_hours if m > 0)

    daily_chart_data = []
    for day, hours in zip(days, daily_hours):
        height_percent = round(
            (hours / longest_session_hours * 100) if longest_session_hours > 0 else 0
        )
        daily_chart_data.append(
            {
                "label": day,
                "hours": round(hours, 1),
                "height_percent": height_percent,
                "is_highlight": hours == longest_session_hours,
            }
        )

    context = {
        "user_stats": {
            "daily_chart_data": daily_chart_data,
            "phone_detections": stats.times_phone_stopped_week,
            "best_day": best_day,
            "best_day_time": format_time_display(best_day_hours),
            "worst_day": worst_day,
            "worst_day_time": format_time_display(worst_day_hours),
            "current_streak": streak_days,
            "total_focus_time": format_time_display(total_focus_hours),
            "daily_average_time": format_time_display(daily_avg_hours),
            "longest_session_time": format_time_display(longest_session_hours),
            "goal_completion_percent": round(goal_completion, 2),
            "sessions_completed": stats.total_sesh_week,
            "focus_percent": round(focus_percentage, 2),
            "distraction_percent": round(100 - focus_percentage, 2),
        }
    }

    return context


def format_time_display(total_hours):
    if total_hours < 1:
        mins = int(total_hours * 60)
        return f"{mins}m"
    else:
        hours = int(total_hours)
        mins = int((total_hours * 60) % 60)
        if mins == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {mins}m"


def reset_if_needed(stats: FocusStats):

    today = timezone.now().date()

    if stats.last_day_reset != today:
        stats.total_sesh_day = 0
        stats.total_focus_time_day = 0
        stats.times_phone_stopped_day = 0
        stats.last_day_reset = today
        stats.save()

    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)

    if stats.last_week_reset < monday:
        stats.total_sesh_week = 0
        stats.total_focus_time_week = 0
        stats.times_phone_stopped_week = 0
        stats.last_week_reset = today
        stats.save()
