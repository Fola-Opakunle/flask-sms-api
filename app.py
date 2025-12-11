
"""
Flask SMS Sender with 3 APIs (Harry Potter, OpenWeather, OpenNotify) via Twilio
-------------------------------------------------------------------------------
- Press a single button to fetch data from:
  1) Harry Potter API (hp-api) - random character details
  2) OpenWeather API - current weather for your configured city
  3) OpenNotify - people currently in space
- Construct a combined message string and send via Twilio SMS.
- Flash a confirmation message using Jinja2.
- Log each sent message as a JSON line in logs/messages.log

Requirements:
  - Set environment variables (see .env.example and README.md).
  - Install dependencies from requirements.txt.

Notes:
  - Twilio trial accounts can only send SMS to verified recipient numbers.
  - All variable names are descriptive; code includes comments explaining key features.
"""
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Tuple

import requests  # For calling external APIs
from flask import Flask, render_template, request, redirect, url_for, flash
from twilio.rest import Client  # Twilio SDK for sending SMS
from dotenv import load_dotenv  # Load .env locally (Replit can also use Secrets)

# Load environment variables from .env (helpful if running locally).
# In Replit, you can set these in "Secrets" and omit the .env file.
load_dotenv()

# Initialize the Flask app.
app = Flask(__name__)
# Secret key is required for flashing messages.
# Use a secure random string in production.
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')

# ----------- Configuration from environment variables -----------
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')
WEATHER_CITY = os.environ.get('WEATHER_CITY', 'Toronto')
WEATHER_COUNTRY_CODE = os.environ.get('WEATHER_COUNTRY_CODE', 'CA')  # Optional
WEATHER_UNITS = os.environ.get('WEATHER_UNITS', 'metric')  # 'metric' or 'imperial'

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')
TWILIO_TO_NUMBER = os.environ.get('TWILIO_TO_NUMBER', '')  # Must be verified for trial accounts

LOG_FILE_PATH = os.path.join('logs', 'messages.log')

# ---------------------- Helper Functions ------------------------
def fetch_random_hp_character() -> Dict[str, Any]:
    """
    Call the Harry Potter API and return a random character.
    API: https://hp-api.onrender.com/api/characters
    Returns a dictionary with selected fields for message formatting.
    """
    url = "https://hp-api.onrender.com/api/characters"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    characters = response.json()

    if not isinstance(characters, list) or len(characters) == 0:
        raise ValueError("Unexpected response from Harry Potter API.")

    character = random.choice(characters)

    # Extract safe fields with defaults to avoid KeyError/None in messages
    name = character.get('name') or 'Unknown Wizard'
    house = character.get('house') or 'Unknown House'
    patronus = character.get('patronus') or 'Unknown Patronus'
    actor = character.get('actor') or 'Unknown Actor'

    return {
        'name': name,
        'house': house,
        'patronus': patronus,
        'actor': actor
    }

def fetch_weather_summary(city: str, country_code: str, units: str) -> Dict[str, Any]:
    """
    Call OpenWeather "Current Weather" endpoint for the given city and return a tidy summary.
    Docs: https://openweathermap.org/current
    Requires: OPENWEATHER_API_KEY

    Returns key weather fields for message formatting.
    """
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OpenWeather API key is missing. Set OPENWEATHER_API_KEY.")

    query = f"{city},{country_code}" if country_code else city
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": query,
        "appid": OPENWEATHER_API_KEY,
        "units": units
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    description = (data.get('weather') or [{}])[0].get('description', 'no description')
    temp = data.get('main', {}).get('temp')
    feels_like = data.get('main', {}).get('feels_like')
    humidity = data.get('main', {}).get('humidity')
    wind_speed = data.get('wind', {}).get('speed')

    return {
        'city': city,
        'country_code': country_code,
        'units': units,
        'description': description,
        'temp': temp,
        'feels_like': feels_like,
        'humidity': humidity,
        'wind_speed': wind_speed
    }

def fetch_astronauts_in_space() -> Dict[str, Any]:
    """
    Call OpenNotify to retrieve the current list of people in space.
    API: http://api.open-notify.org/astros.json
    Returns count and a list of names for message formatting.
    """
    url = "http://api.open-notify.org/astros.json"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()

    if data.get('message') != 'success':
        raise ValueError("OpenNotify did not return success.")

    people = data.get('people', [])
    names = [p.get('name', 'Unknown') for p in people]
    return {
        'count': data.get('number', len(names)),
        'names': names
    }

def format_message(hp: Dict[str, Any], weather: Dict[str, Any], space: Dict[str, Any]) -> str:
    """
    Combine pieces from the three APIs into a single human-friendly message string.
    Example output:
      "Weather in Toronto: 12°C, clear sky. Fun fact: Hermione Granger (Gryffindor, Patronus: Otter).
       There are 7 people in space right now: ..."
    """
    # Build weather part with units label
    if weather['units'] == 'metric':
        temp_unit = '°C'
        wind_unit = 'm/s'
    else:
        temp_unit = '°F'
        wind_unit = 'mph'

    weather_part = (
        f"Weather in {weather['city']}: {weather['temp']}{temp_unit}, "
        f"feels like {weather['feels_like']}{temp_unit}, "
        f"{weather['description']}, humidity {weather['humidity']}%, "
        f"wind {weather['wind_speed']} {wind_unit}."
    )

    hp_part = (
        f" Wizarding note: {hp['name']} (House: {hp['house']}, Patronus: {hp['patronus']})."
    )

    # Include up to first 5 astronaut names to keep message concise
    astronaut_names = ', '.join(space['names'][:5]) if space['names'] else 'N/A'
    space_part = (
        f" People in space right now: {space['count']}"
        + (f" ({astronaut_names})" if astronaut_names != 'N/A' else "") + "."
    )

    return f"{weather_part}{hp_part}{space_part}"

def send_sms_via_twilio(body_text: str) -> Dict[str, Any]:
    """
    Send SMS using Twilio. Requires environment variables:
      - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
      - TWILIO_FROM_NUMBER (Twilio phone number)
      - TWILIO_TO_NUMBER (Your verified recipient on trial)
    Returns a small dict with status and sid for logging.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER]):
        raise RuntimeError("Twilio configuration is incomplete. Set all required env variables.")

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        body=body_text,
        from_=TWILIO_FROM_NUMBER,
        to=TWILIO_TO_NUMBER
    )
    return {"sid": msg.sid, "status": getattr(msg, "status", "unknown")}

def append_json_log(record: Dict[str, Any]) -> None:
    """
    Append a JSON record to logs/messages.log as a single JSON line (JSONL).
    Creates the file if it does not exist.
    """
    # Ensure logs directory exists.
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

# --------------------------- Routes -----------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    GET: Render a page with one button ("Send Message").
    POST: On button press, call the three APIs, construct the message,
          send it via Twilio, flash a success message, and log the result.
    """
    if request.method == 'POST':
        try:
            # Call the three external APIs
            hp = fetch_random_hp_character()
            weather = fetch_weather_summary(WEATHER_CITY, WEATHER_COUNTRY_CODE, WEATHER_UNITS)
            space = fetch_astronauts_in_space()

            # Build the SMS body
            message_text = format_message(hp, weather, space)

            # Send it via Twilio
            twilio_result = send_sms_via_twilio(message_text)

            # Create a structured log record
            log_record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": message_text,
                "twilio_sid": twilio_result.get("sid"),
                "twilio_status": twilio_result.get("status"),
                "weather_city": WEATHER_CITY,
                "weather_country_code": WEATHER_COUNTRY_CODE
            }
            append_json_log(log_record)

            # Flash success info to the user
            flash("SMS sent successfully! (SID: {})".format(twilio_result.get("sid")), "success")
            return redirect(url_for('index'))

        except Exception as exc:
            # Log error details for troubleshooting
            error_record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(exc)
            }
            append_json_log(error_record)

            flash("Failed to send SMS: {}".format(str(exc)), "error")
            return redirect(url_for('index'))

    # GET request renders the template with the Send button
    return render_template('index.html')

if __name__ == '__main__':
    # When running locally: python app.py
    # For Replit, the web server will run on the assigned port.
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' allows external access in hosted environments like Replit
    app.run(host='0.0.0.0', port=port, debug=True)
