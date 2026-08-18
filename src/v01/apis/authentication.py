import jwt
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import SecretStr

from datetime import UTC, datetime, timedelta

# directly import the google db for the data
from google.cloud import bigquery


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin/token")

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None=None) -> str:
    # creating JWT token
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=30
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SecretStr.get_secret_value(),
        "HS256"
    )

    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SecretStr.get_secret_value(),
            "HS256",
            options={"require": ["exp", "sub"]}
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")

auth = APIRouter()

@auth.post("auth/signin")
async def signin_direct():
    pass