# MetaCog OS

**Reclaim your focus. Reclaim your learning. Reclaim your future.**

MetaCog OS is an integrated AI-powered productivity and learning ecosystem designed to transform how students and professionals approach focus, learning, and growth. Built by a student, for students—because we understand the struggle of AI dependency, distraction, and surface-level learning.

---

## The Problem

In an age of "vibe coding" and instant AI answers, we're stuck in what we call **"AI Hell"**—where you *know* the content but can't actually *do* it. LLMs hand you solutions, but do you learn? Not really.

Meanwhile, distractions are everywhere. Your phone. That tab. That notification. Focus feels impossible.

**MetaCog OS solves both.**

---

## What is MetaCog OS?

MetaCog OS is a comprehensive system that supports you **before, during, and after** your study sessions:

### **Before You Study: FocusAI**
Your personal AI accountability system that prevents smartphone distractions in real-time.

### **During Your Study: Saathi**
An AI tutor that guides you through problems instead of solving them for you—breaking the cycle of AI dependency.

### **After You Study: Analytics & Insights**
Comprehensive performance tracking, AI-generated weekly reports, and automated revision quizzes to ensure retention.

---

## FocusAI: Your Personal AI Accountability System

Real-time distraction detection powered by computer vision and AI.

### Features:
- **Real-Time Distraction Detection**
  - AI-powered computer vision detects phone usage during focus sessions
  - Detects tab switches to keep you on task
  - Toggle detection on/off anytime via settings
  - Instant accountability with timer pause and alert sounds

- **Comprehensive Analytics Dashboard**
  - Weekly focus data visualization with bar graphs
  - Best/worst day performance comparisons
  - Session duration analysis
  - Focus-to-distraction ratios via interactive donut charts

- **Built-In Productivity Tools**
  - Integrated to-do lists—no need for external apps
  - Seamless workflow without app-switching
  - AI-powered text summarization (Gemini Model) for research and study sessions

---

## Saathi: The Anti-Dependency AI Tutor

**"Not a single LLM built for learning? We built one."**

Saathi isn't just another chatbot. It's designed to **guide, not solve**—to help you grow, not create dependency.

### The Saathi Philosophy:
> *Automation should remove friction, not thinking. The mental strain is where learning happens.*

### Features:

#### **Context-Aware AI Chat**
- Powered by Gemini 2.5 Flash for low latency and reliable reasoning
- Breaks down complex STEM problems into digestible steps
- **Never gives direct answers**—it guides you to the solution
- Context-aware reasoning for accurate, meaningful responses

#### **Instant Quiz Generation**
- Upload PDFs, .txt, .docx, or paste text
- Generates 5-20 question MCQ quizzes in seconds
- Supports mixed input (text + document) for comprehensive quizzes
- Perfect for active recall practice

#### **Intelligent Performance Tracking**
- Chart.js visualizations showing accuracy trends across your last 10, 15, 20, 25, and 30 quizzes
- Overall statistics dashboard: total quizzes, questions answered, current streak
- **Brutal reality check**: see exactly where you stand

#### **Automatic Revision System**
- After 15 wrong answers, Saathi auto-generates a revision quiz
- Forces you to confront your weak spots
- No more avoiding what you don't know

#### **Personalized Learning Prompts**
- After each quiz, get a custom prompt explaining what you missed and why
- Copy-paste into Saathi's chat for targeted explanations
- Bridges the gap between practice and understanding

---

## Portal: The Integration Hub

MetaCog OS isn't just two separate apps—it's a unified system.

### Weekly AI Reports
- Generated every Sunday
- Analyzes performance across **both FocusAI and Saathi**
- Identifies patterns, strengths, and areas for improvement
- Actionable insights to optimize your learning workflow

---

##  The MetaCog Narrative

**MetaCog OS is the only system that supports you throughout your entire learning journey:**

1. **BEFORE:** Keeps you accountable and focused when you're studying (FocusAI)
2. **DURING:** Helps you learn by guiding, not solving (Saathi Chat)
3. **AFTER:** Reinforces learning through quizzes, feedback, and AI reports (Saathi Analytics + Portal)
4. **PROACTIVE:** Auto-generates revision quizzes after 15 mistakes

> *Humans can coach you DURING study time. But after? They can't. That's what MetaCog OS solves.*

---

## Tech Stack

- **Backend:** Django
- **Database:** PostgreSQL and Supabase for auth
- **AI Models:** 
  - Gemini 2.5 Flash 
  - Cerebras 
  - PyTorch (AI model for CV)
- **Frontend:** HTML, Tailwind CSS, JavaScript, Chart.js
- **Computer Vision:** OpenCV, PyTorch

---

##  Setup Guide

### Prerequisites
- Python 3.12
- PostgreSQL 
- Supabase project
- Webcam (for FocusAI distraction detection)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aruniaaa/MetaCog-OS
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your `.env` file**
   
   Create a `.env` file in the root directory with the following variables:
   
   ```env
   # Database
   DB_PASS=your_postgresql_password
   
   # Supabase 
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   
   # AI API Keys
   GEMINI_KEY=your_gemini_api_key
   CEREBRAS_API_KEY=your_cerebras_api_key
   
   # Django Settings
   DEBUG=True
   SECRET_KEY=your_django_secret_key
   ```
   
   **How to get API keys:**
   - **Gemini API Key:** Get it from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **Cerebras API Key:** Sign up at [Cerebras Cloud](https://cloud.cerebras.ai/)
   - **Supabase:** Create a project at [Supabase](https://supabase.com/)
   - **Django Secret Key:** Generate one using:


5. **Download the FocusAI model**
   
   The PyTorch model will automatically download on first run. If you encounter issues, ensure you have a stable internet connection.

6. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
    
    Open your browser and navigate to `http://127.0.0.1:8000/`

10. **Leave a review!**

    MetaCog OS is a web app for students, by a student. And it needs your constructive criticism to grow. So, don't be shy, try the app out, and let me know what you think!

    You can reach out to me via the email listed below.
---

## Usage

### FocusAI
1. Navigate to the FocusAI section
2. Enable distraction detection in Settings
3. Start a focus session
4. Stay focused—FocusAI will alert you if it detects your phone or tab switches
5. Use the built in tools like AI text summarization and to-do lists to manage your time efficiently
6. Keep visiting the stats page every once in a while for motivation (and a reality check)

### Saathi
1. Navigate to Saathi
2. **Chat:** Ask questions and get guided explanations
3. **Quiz:** Upload study materials or paste text to generate quizzes
4. **Analytics:** Track your progress and identify weak spots
5. **Revision:** Complete auto-generated revision quizzes after 15 mistakes

### Portal
1. Check your weekly AI reports every Sunday
2. View integrated analytics from both FocusAI and Saathi

---

## Troubleshooting

### Model Loading Error
If you see `invalid load key, '<'`:
- Ensure the model file downloaded correctly
- Delete `FocusAI/cnn-models/pytorch_model.pt` and restart the server to re-download

### Database Connection Issues
- Verify your `DB_PASS` in the `.env` file
- Ensure PostgreSQL is running 
- Check Supabase credentials 

### API Rate Limits
- Both Gemini and Cerebras have free tier rate limits
- Consider upgrading your API plan if you hit limits frequently

---

## Support

Running into errors or missing files? Have questions or feedback?

**Contact:** charulabs@gmail.com

I'm here to help! Don't hesitate to reach out.

---

## License

Copyright (c) 2025 Charu Singhania

All rights reserved.

---

## Acknowledgments

Built with frustration, caffeine, and the belief that learning should build you up, not make you dependent.

**MetaCog OS: Focus. Learn. Grow.**