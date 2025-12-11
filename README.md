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
## What Could Be Improved

This project can be extended in several ways to make it more production-ready:

1. **Authentication**
   - Currently, anyone who knows the endpoint URL can send a request.
   - Add an API key, JWT, or token-based authentication layer.

2. **Input Validation**
   - Use a library like `pydantic` or `marshmallow` to enforce strict data schemas.
   - Validate phone number format with regex or a library.

3. **Error Handling**
   - Improve the granularity of error messages (e.g., provider errors vs. client errors).
   - Log errors to a file or monitoring tool.

4. **Logging**
   - Implement an audit log of all SMS requests.
   - Store request metadata (IP, timestamp, message length).

5. **Testing**
   - Add unit tests using `pytest` to test the API route and SMS client.
   - Mock external API calls so the tests run without a real SMS provider.

6. **Rate Limiting**
   - Prevent abuse by limiting the number of requests per minute per client.

7. **Deployment**
   - Containerize the app using Docker.
   - Deploy to Render, Railway, AWS, or Azure.

8. **Production Server**
   - Use Gunicorn or Uvicorn behind Nginx instead of Flask’s dev server.

These improvements turn a simple demo into a deployment-ready microservice.

## Project Structure

```text
flask-sms-api/
├─ app.py
├─ requirements.txt
├─ README.md
└─ .gitignore
