# Flask SMS API

This project is a simple Flask-based SMS API that exposes an HTTP endpoint
for sending text messages through an external SMS provider (e.g. Twilio).

It’s designed to be a clean, minimal example of how to:

- Structure a small Flask API
- Read configuration from environment variables
- Call a third-party API from a backend service
- Return clear JSON responses

---

## Features

- `POST /send-sms` endpoint
- Validates required fields (`to`, `message`)
- Uses environment variables for API keys and phone numbers
- Returns JSON with success or error details
- Easy to extend with logging, database storage, or more endpoints

---

## Tech Stack

- **Language:** Python
- **Framework:** Flask
- **SMS Provider:** Twilio (or similar)
- **Environment:** Any machine with Python 3.x installed

---

## Project Structure

```text
flask-sms-api/
├─ app.py
├─ requirements.txt
├─ README.md
└─ .gitignore
