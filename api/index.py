import os
#os helps us to access other files in the main folder of the project
import sys
from flask import Flask, render_template, request, jsonify
#flask is the medium that connects the front end and backend
from datetime import datetime, timedelta
#accessing the date and the time
from dotenv import load_dotenv
#we have a .env file that contains the API key for the AI client, so we use dotenv to load it into the environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#appends the directories in the main folder
from ai_helper import generate_productivity_data, generate_chat_response
#calls ai helper.py to access the functions that generate productivity data and chat responses

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '..', 'templates')

app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def home():
    return render_template('index.html', google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""))
#home() calls the google client ID and activatees the frontend (index.html)

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    mode = data.get('mode')
    user_input = data.get('input_data')
    force = data.get('force', False)
    #mode = which user the user is working on (booster, milestones etc)
    #user input = the data that the user has provided to the AI model
    #force = when the user clicks the button, it sets force to true, which forces the AI model to generate a new response even if the input data hasn't changed. This is useful for users who want to see different variations of the output or if they feel the previous output was not satisfactory.
    
    if not mode or not user_input:
        return jsonify({"error": "Missing selection parameters or input details"}), 400
        
    ai_response = generate_productivity_data(mode, user_input, force=force)
    #calls the generate productivity function from ai_helper.py tp generate the AI response.
    return jsonify({"result": ai_response})

@app.route('/api/chat', methods=['POST'])
def chat():
    #gets the data from the user and generates a response. can handle images and stuff
    data = request.get_json() or {}
    message = data.get('message')
    base64_image = data.get('image')
    image_mime = data.get('image_mime')
    context = data.get('context')
    force = data.get('force', False)
    
    if not message:
        return jsonify({"error": "Message body cannot be empty"}), 400
        
    chat_response = generate_chat_response(message, base64_image, image_mime, context, force=force)
    return jsonify({"result": chat_response})

@app.route('/api/calendar/create', methods=['POST'])
def create_calendar_event():
    #get dates of exam (calendar selection) and use that to create an event in the google calendar.
    data = request.get_json() or {}
    token = data.get('token')
    title = data.get('title')
    date_str = data.get('date')
    description = data.get('description')
    #what the user has to do (description)
    
    if not token or not title or not date_str:
        return jsonify({"error": "Missing required Google Calendar event parameters."}), 400
        
    if token == "mock_developer_access_token":
        return jsonify({"success": True, "mock": True})

    try:
        #call the httpx library to make a connection to the google calendar.
        import httpx
        try:
            start_dt = datetime.strptime(date_str, "%Y-%m-%d")
            end_date_str = (start_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception:
            end_date_str = date_str

        event_payload = {
            "summary": title,
            "description": description,
            "start": {"date": date_str},
            "end": {"date": end_date_str}
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        res = httpx.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=headers,
            json=event_payload,
            timeout=15.0
        )
        
        if res.status_code in [200, 201]:
            return jsonify({"success": True, "result": res.json()})
        else:
            return jsonify({"error": f"Google API Error {res.status_code}: {res.text}"}), res.status_code
            
    except Exception as e:
        return jsonify({"error": f"Internal sync connection failure: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
