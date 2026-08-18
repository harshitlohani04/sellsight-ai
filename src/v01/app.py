from fastapi import FastAPI, APIRouter
from .apis import mail_data_api, gmail_reader

main = FastAPI()

main.include_router(mail_data_api.app)
main.include_router(gmail_reader.app)

@main.get('/')
async def root():
    return {'message': 'Welcome to the sellsight ai'}
