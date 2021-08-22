from pydantic import BaseSettings

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyQuery
from datetime import datetime

class Settings(BaseSettings):
    zythogora_db_username: str
    zythogora_db_password: str

    class Config:
        env_file = "db_credentials"

settings = Settings()



import mysql.connector as database

connection = database.connect(
    user=settings.zythogora_db_username,
    password=settings.zythogora_db_password,
    host="localhost",
    database="Zythogora"
)

cursor = connection.cursor(prepared=True)



key = APIKeyQuery(name="api-key", auto_error=False)
async def get_api_key(request: Request, key: str = Security(key)):
    cursor.execute(
        "SELECT id, user, api_key, is_dev, iat, exp " +
        "FROM API_Keys " +
        "WHERE api_key = %s"
    , (key,))
    query_apikey = cursor.fetchone()

    if not query_apikey:
        raise HTTPException(status_code=403, detail="Invalid API Key.")

    if query_apikey[5] < datetime.now():
        raise HTTPException(status_code=403, detail="Invalid API Key.")

    cursor.execute(
        "INSERT INTO API_Requests " +
        "(api_key, method, endpoint, ip, port) " +
        "VALUES (%s, %s, %s, %s, %s)"
    , (
        key,
        request.method,
        request.url.path,
        request.client.host,
        request.client.port
    ))
    connection.commit()

    return {
        "user": query_apikey[1],
        "api_key": query_apikey[2],
        "is_dev": query_apikey[3]
    }
