import httpx
import json

# Test login
url = "http://localhost:8000/api/auth/login"
data = {"email": "doctor@hospital.com", "password": "demo123"}

try:
    with httpx.Client() as client:
        response = client.post(url, json=data)
        print("Status:", response.status_code)
        print("Response:", response.text)
except Exception as e:
    print("Error:", type(e).__name__, str(e))