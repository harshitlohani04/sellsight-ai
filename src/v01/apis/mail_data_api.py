from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import RedirectResponse

from .gmail_app import (
    create_authorization_url,
    exchange_code_for_credentials,
    create_gmail_service
)

from email.mime.text import MIMEText
from email.mime.base  import MIMEBase
from email import encoders

import os


version = 'v1'
service_type = 'gmail'
user = 'kartiklohani2004@gmail.com' #hardcoded for now
TOKEN_JSON = os.path.join(os.getcwd(), f"token_{version}_{service_type}_{user}.json")

app = APIRouter()

def upload_token_2_bucket(token_file):
    pass


@app.get("/auth/gmail")
async def gmail_auth():

    authorization_url, state, code_verifier = create_authorization_url()

    response = RedirectResponse(
        url=authorization_url,
        status_code=302
    )

    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        path="/"
    )

    response.set_cookie(
        key="oauth_code_verifier",
        value=code_verifier,
        httponly=True,
        samesite="lax",
        path="/"
    )

    return response

@app.get("/auth/gmail/callback")
async def gmail_callback(
    request: Request,
    code: str,
    state: str
):
    print(request.cookies)
    stored_state = request.cookies.get("oauth_state")

    code_verifier = request.cookies.get("oauth_code_verifier")

    if not stored_state:
        return {"error": "OAuth state not found"}

    if not code_verifier:
        return {"error": "OAuth code verifier not found"}

    if state != stored_state:
        return {"error": "Invalid OAuth state"}

    try:

        credentials = exchange_code_for_credentials(
            code=code,
            state=state,
            code_verifier=code_verifier
        )

        # print(credentials.to_json())

        # service = create_gmail_service(credentials)

        # profile = service.users().getProfile(
        #     userId="me"
        # ).execute()

        # email = profile.get("emailAddress")

        # return {
        #     "message": "Gmail connected successfully",
        #     "email": email
        # }

        ''' Storing the credentials in a json file for further requests '''
        with open(TOKEN_JSON, 'w+') as file:
            file.write(credentials.to_json())
        file.close()
        
        return RedirectResponse("/fetch/email")

    except Exception as e:

        return {
            "error": str(e)
        }