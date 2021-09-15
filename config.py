from pydantic import BaseSettings

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyQuery
from datetime import datetime

class Settings(BaseSettings):
    zythogora_db_username: str
    zythogora_db_password: str
    zythogora_db_host:     str
    zythogora_db_database: str

    class Config:
        env_file = "db_credentials"

settings = Settings()



import mysql.connector as database

connection = database.connect(
    user=settings.zythogora_db_username,
    password=settings.zythogora_db_password,
    host=settings.zythogora_db_host,
    database=settings.zythogora_db_database
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



from pyjarowinkler.distance import get_jaro_distance

async def search(search_term: str, term_query, count: int = 10):
    search_term = search_term.lower()

    res = [ ]
    contains = [ ]
    jaro_winkler = { }
    for el in term_query:
        term = el[1].lower()

        if term.startswith(search_term):
            res.append(el[0])

            if len(res) == count:
                return res

        elif search_term in term:
            contains.append(el[0])

        else:
            jaro_winkler[el[0]] = get_jaro_distance(search_term, term, winkler=True)

    if len(res) + len(contains) >= count:
        return res + contains[:(count - len(res))]

    jaro_winkler = [ k for k, v in sorted(jaro_winkler.items(), key=lambda item: item[1]) ]
    jaro_winkler.reverse()

    return res + contains[:(count - len(res))] + jaro_winkler[:(count - len(res) - len(contains))]
