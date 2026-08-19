from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


CLIENT_SECRET_FILE = "client-secret-file.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

REDIRECT_URI = "http://127.0.0.1:8000/auth/gmail/callback"


def create_authorization_url():

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES
    )

    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return authorization_url, state, flow.code_verifier


def exchange_code_for_credentials(
    code: str,
    state: str,
    code_verifier: str
):

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        state=state
    )

    flow.redirect_uri = REDIRECT_URI

    # Restore the PKCE verifier generated
    # during the initial authorization request.
    flow.code_verifier = code_verifier

    flow.fetch_token(code=code)

    return flow.credentials


def create_gmail_service(credentials: Credentials):

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )