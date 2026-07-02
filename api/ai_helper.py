import os
#how to get to get to all files located in the main folder of the project
from groq import Groq
#Groq for the AI client
from dotenv import load_dotenv
#we have a .env file that contains the API key for the AI client, so we use dotenv to load it into the environment variables
from datetime import datetime

load_dotenv()

#load the API key and check that the API key is loaded. If it isn't, give an error to the user
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GROQ_API_KEY is missing from your environment variables!")
    return Groq(api_key=api_key)

#connect with the Groq client, generate an error if the user has not provided an error.
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

        #date/time function that provides the current date on which the user is
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        #defines prompt structure for each mode 
        if mode == "planner":
            prompt = (
                f"Today's Date: {today_str}. Create an optimized high school exam preparation study roadmap. "
                f"Exam Date: {user_input.get('exam_date')}. Subjects and current student confidence parameters: {user_input.get('subjects')}. "
                "Break this down systematically into chronological milestones. For each milestone block, prefix it with an explicit single-line tag in the exact format [DATE: YYYY-MM-DD] indicating when the user should finish that milestone."
            )
        elif mode == "milestone":
            prompt = (
                f"Today's Date: {today_str}. Break down the following high school project into structured milestone checkpoints. "
                f"Project Title: {user_input.get('title')}. Assignment Requirements: {user_input.get('requirements')}. "
                f"Final Submission Deadline: {user_input.get('deadline')}. "
                "Structure into clear chronological sequence checkpoints. For each checkpoint block, prefix it with an explicit single-line tag in the exact format [DATE: YYYY-MM-DD] indicating when the checkpoint should be completed."
            )
        elif mode == "booster":
            prompt = (
                f"Today's Date: {today_str}. Build an accelerated step-by-step study session plan for today. "
                f"Tasks to accomplish: {user_input.get('tasks')}. Total focus window time capacity: {user_input.get('hours')} hours. "
                "Calibrate the time blocks to fit exactly within the requested hour limit."
            )
        #response gives instructions to the AI model to provide a structured output in Markdown format, with specific tags for dates and milestones. The AI model is expected to return a clear, actionable plan based on the user's input.
        response = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {"role": "system", "content": "You are ScholarSync AI's expert academic productivity coordinator. Provide strategic, actionable high school study guidance and roadmaps using clear, clean Markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Optimization Pipeline Error: {str(e)}"

#we ask a question, the AI chatbot gives us a response. The system prompt is a set of instructions that tells the AI model how to behave and what kind of responses to generate. The system prompt is designed to make the AI model act as a helpful and knowledgeable assistant for high school students, providing guidance on homework, study tasks, and understanding complex concepts. The system prompt also tells the model to provide only the final answer and to avoid any internal reasoning or <tool_call>/<think> tags.
def generate_chat_response(message, base64_image=None, image_mime=None, current_context=None, force=False):
    try:
        client = get_groq_client()
        
        system_prompt = (
            "You are ScholarSync AI's Homework & Study Companion chatbot. Your objective is to help high school students "
            "comprehend assignments, analyze provided homework images/files, break down complex concepts, and support study tasks. "
            "Keep your explanations educational, concise, highly supportive, and formatted cleanly using simple Markdown tags. "
            "The most important part is to answer directly with the final response only. Do not include any internal reasoning, analysis, hidden chain-of-thought, or <think> / <tool_call> tags."
        )
        if not force:
            system_prompt += " If the user query or text is absolute gibberish, random keystrokes, or spam, you must output ONLY the exact text string: GIBBERISH_DETECTED"
            
        if current_context:
            system_prompt += f" Keep in mind that the student is currently focusing on this specific phase objective: {current_context}"

        #the question the user will ask is the content_payload
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
