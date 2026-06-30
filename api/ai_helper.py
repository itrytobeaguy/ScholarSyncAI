import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GROQ_API_KEY is missing from your environment variables!")
    return Groq(api_key=api_key)

def generate_productivity_data(mode, user_input, force=False):
    try:
        client = get_groq_client()
        
        if not user_input or not isinstance(user_input, dict):
            return "Validation Error: No configuration input packet was provided."

        if mode == "planner":
            if not user_input.get('exam_date') or not user_input.get('subjects'):
                return "Validation Error: Please ensure an Exam Date and Subject confidence log are filled out."
        elif mode == "milestone":
            if not user_input.get('title') or not user_input.get('requirements') or not user_input.get('deadline'):
                return "Validation Error: Please ensure Project Title, Requirements, and Deadlines are completely filled out."
        elif mode == "booster":
            if not user_input.get('tasks') or not user_input.get('hours'):
                return "Validation Error: Please list your Tasks and available study Hours."

        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        
        target_date_str = ""
        if mode == "planner":
            target_date_str = user_input.get('exam_date', '')
        elif mode == "milestone":
            target_date_str = user_input.get('deadline', '')

        days_rem = 0
        distribution_style = "daily blocks"
        distribution_instruction = (
            "Because the timeline is immediate, you must distribute the plan day-by-day. "
            "Every distinct day must start exactly with a markdown header containing the date tag formatted as: "
            "`### [DATE: YYYY-MM-DD] Day X: Task Title`."
        )

        if target_date_str:
            try:
                target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
                days_rem = (target_dt - today).days
                
                if 7 < days_rem <= 30:
                    distribution_style = "weekly blocks pinned to Mondays"
                    distribution_instruction = (
                        "Because the timeline spans multiple weeks, you must distribute the plan week-by-week. "
                        "You must schedule each milestone strictly on the Mondays falling within this date range. "
                        "Every single weekly entry must start exactly with a markdown header containing the date tag formatted as: "
                        "`### [DATE: YYYY-MM-DD] Week X: Focus Objective` where the date is a valid calendar Monday."
                    )
                elif days_rem > 30:
                    distribution_style = "bi-monthly blocks pinned to the 1st and 15th"
                    distribution_instruction = (
                        "Because the timeline spans months, you must distribute the plan across specific monthly intervals. "
                        "You must schedule milestones strictly on the 1st of the month and the 15th of the month falling within this range. "
                        "Every single distributed entry must start exactly with a markdown header containing the date tag formatted as: "
                        "`### [DATE: YYYY-MM-DD] Month Milestone` where the date is strictly the 1st or 15th day of a calendar month."
                    )
            except Exception:
                pass

        timezone_mandate = (
            f"\nToday's current date is explicitly {today_str}. The duration until the event is {days_rem} days. "
            f"You must strictly distribute the schedule into {distribution_style}.\n{distribution_instruction}\n"
            f"CRITICAL SYSTEM RULE: Each date section header MUST contain the exact `[DATE: YYYY-MM-DD]` token string so our parsing engine can automatically extract and create separate individual calendar entries."
        )

        thinking_and_spam_guard = (
            "\nCRITICAL PRIVACY & QUALITY MANDATE: Do not include any internal reasoning, thoughts, or <think> tags in your output. "
            "Provide only the direct final response. "
        )
        if not force:
            thinking_and_spam_guard += "If the input provided consists of absolute gibberish, nonsensical letters, or spam, reply ONLY with the exact string: GIBBERISH_DETECTED"

        if mode == "planner":
            system_prompt = (
                "You are ScholarSync AI's Core Exam Planner. Build a high school level distributed preparation schedule "
                "prioritizing weaker subjects based on the provided logs." + timezone_mandate + thinking_and_spam_guard
            )
            user_content = f"Today's Date: {today_str}\nExam Date: {user_input.get('exam_date')}\nSubject Logs: {user_input.get('subjects')}"
            
        elif mode == "milestone":
            system_prompt = (
                "You are ScholarSync AI's Milestone Project Assistant. Break the project down into clear, incremental micro-deadlines. "
                "At the very end of your response, provide a '🌐 Recommended Research Gateways' section recommending "
                "safe digital archives or free tools tailored exactly to this assignment." + timezone_mandate + thinking_and_spam_guard
            )
            user_content = f"Today's Date: {today_str}\nProject Title: {user_input.get('title')}\nRequirements: {user_input.get('requirements')}\nDeadline: {user_input.get('deadline')}"
            
        elif mode == "booster":
            system_prompt = (
                f"You are ScholarSync AI's Daily Booster. Take the tasks and time available, then create an actionable micro-schedule "
                f"using the Pomodoro methodology. You MUST strictly build this schedule around the user's custom choice of exactly {user_input.get('hours')} hours. "
                f"Do not invent or extend this timeframe automatically. Include brief 5-minute brain-break resource ideas." + timezone_mandate + thinking_and_spam_guard
            )
            user_content = f"Today's Date: {today_str}\nTasks: {user_input.get('tasks')}\nAvailable Time: {user_input.get('hours')} hours"
            
        else:
            return "Invalid operational mode selected."

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.6,
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Backend Error: {str(e)}"

def generate_chat_response(message, base64_image=None, image_mime=None, current_context=None, force=False):
    try:
        client = get_groq_client()
        
        system_prompt = (
            "You are ScholarSync AI's Homework & Study Companion chatbot. Your objective is to help high school students "
            "comprehend assignments, analyze provided homework images/files, break down complex concepts, and support study tasks. "
            "Keep your explanations educational, concise, highly supportive, and formatted cleanly using simple Markdown tags. "
            "CRITICAL QUALITY MANDATE: Do not show or include your internal thinking process, reasoning steps, or <think> tags anywhere. "
        )
        if not force:
            system_prompt += "If the user query or text is absolute gibberish, random keystrokes, or spam, you must output ONLY the exact text string: GIBBERISH_DETECTED"
            
        if current_context:
            system_prompt += f" Keep in mind that the student is currently focusing on this specific phase objective: {current_context}"

        content_payload = []
        content_payload.append({"type": "text", "text": message})
        
        if base64_image and image_mime:
            content_payload.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_mime};base64,{base64_image}"
                }
            })

        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_payload}
            ],
            temperature=0.5,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Chat Error: {str(e)}"