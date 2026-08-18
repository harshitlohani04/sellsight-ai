from .gmail_app import create_gmail_service
from .mail_data_api import TOKEN_JSON

from google.oauth2.credentials import Credentials

from fastapi import FastAPI, APIRouter

import json
import os

app = APIRouter()

def get_creds():
    json_path = os.path.join(os.getcwd(), TOKEN_JSON)
    
    creds = Credentials.from_authorized_user_file(json_path, scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    return creds

@app.get('/fetch/email')
async def fetch_mail_data():

    credentials = get_creds()

    service = create_gmail_service(credentials=credentials)
    profile = service.users().getProfile(
        userId="me"
    ).execute()
    email = profile.get("emailAddress")

    return {
        "message": "Gmail connected successfully",
        "email": email
    }

