import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from upstash_redis import Redis

# --- Constants ---
UPSTASH_REDIS_REST_URL = "https://fine-swift-52766.upstash.io"
UPSTASH_REDIS_REST_TOKEN = "Ac4eAAIjcDE2NzI4ZmMzYmU1NmU0NmM3ODIxY2YzYWI2ZTAyMzdhNXAxMA"
SCOPES = ['https://www.googleapis.com/auth/calendar']
DEFAULT_DURATION_MINUTES = 60  # Default meeting duration: 1 hour

# Initialize Redis client
redis_client = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)

# Check and install dependencies dynamically
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
except ImportError:
    print("Installing required libraries...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                           "google-auth", "google-auth-oauthlib", "google-api-python-client"])
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

# Obfuscated credentials JSON parts
part1 = '{"installed":{"client_id":"524902306963-'
part2 = 'hfkqghvd9jlluoeho4hp3dban2abqhb1.apps.googleusercontent.com",'
part3 = '"project_id":"calender-445015","auth_uri":"https://accounts.google.com/o/oauth2/auth",'
part4 = '"token_uri":"https://oauth2.googleapis.com/token",'
part5 = '"auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",'
part6 = '"client_secret":"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",'
part7 = '"redirect_uris":["http://localhost"]}}'

# Combine parts to reconstruct the JSON
json_data = part1 + part2 + part3 + part4 + part5 + part6 + part7


def authenticate_user():
    """
    Authenticate the user via OAuth2 and return a Google Calendar API service object.
    Saves token for future runs.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        credentials_info = json.loads(json_data)
        flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"Error initializing Google Calendar API service: {e}")
        sys.exit(1)


def create_meeting(service, summary, description, start_time, time_zone):
    """
    Create a Google Calendar meeting with the specified details.
    """
    print(f"Start Time Received: {start_time}")
    if isinstance(start_time, str):
        try:
            start_time = datetime.fromisoformat(start_time)
        except ValueError:
            print("\u26A0\uFE0F Invalid start_time format. Expected 'YYYY-MM-DDTHH:MM:SS'.")
            return

    end_time = start_time + timedelta(minutes=DEFAULT_DURATION_MINUTES)
    print(f"End Time Calculated: {end_time}")

    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': time_zone},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': time_zone},
        'reminders': {'useDefault': True},
    }

    try:
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        redis_client.set("meeting_link", event_result['htmlLink'])
        print(f"✅ Meeting has been successfully scheduled!\nEvent details: {event_result['htmlLink']}")
    except Exception as e:
        print(f"Error creating event: {e}")


def get_valid_datetime_input(prompt):
    """
    Prompt user for a valid date-time input and return a datetime object.
    """
    while True:
        try:
            date_input = input(prompt)
            return datetime.strptime(date_input, "%Y-%m-%d %H:%M")
        except ValueError:
            print("\u26A0\uFE0F Invalid format. Please use 'YYYY-MM-DD HH:MM'.")


def main():
    print("\n🔹 Welcome to the Automated Meeting Scheduler 🔹\n")
    print("Note: You will be asked to log in with your Google account.\n")
    service = authenticate_user()

if __name__ == "__main__":
    main()
