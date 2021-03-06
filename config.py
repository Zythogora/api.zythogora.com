from argon2 import PasswordHasher
from datetime import datetime
from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyQuery
import jwt
import mysql.connector as database
import os
from pyjarowinkler.distance import get_jaro_distance



connection = database.connect(
    user     = os.environ["zythogora_db_username"],
    password = os.environ["zythogora_db_password"],
    host     = os.environ["zythogora_db_host"],
    database = os.environ["zythogora_db_database"]
)




key = APIKeyQuery(name="api-key", auto_error=False)
async def get_api_key(request: Request, key: str = Security(key)):

    # Refresh connection if needed

    connection.ping(reconnect=True)

    # No Auth

    no_auth = [
        [ "POST", "/users/login" ],
        [ "POST", "/users/register" ],
    ]

    if request.method == "GET":
        return {}

    if [ request.method, request.url.path ] in no_auth:
        return {}


    # JWT Auth

    jwt_header = request.headers.get("Authorization")
    if jwt_header:
        try:
            token = jwt.decode(jwt_header, os.environ["zythogora_jwt_secret"], algorithms=["HS512"])
            return {
                "user": token["client_id"],
                "exp": token["exp"]
            }
        except:
            raise HTTPException(status_code=401, detail="Unauthorized")


    # API Key Auth

    with connection.cursor(prepared=True) as cursor:
        if not key:
            raise HTTPException(status_code=401, detail="Unauthorized")

        cursor.execute("""
            SELECT id, user, key_hash, permissions, is_dev, iat, exp
            FROM API_Keys
            WHERE key_help LIKE %s
        """, (key[:4] + "%" + key[31:],))
        query_apikey = cursor.fetchall()

        if not query_apikey:
            raise HTTPException(status_code=403, detail="Invalid API Key.")

        api_key = None
        for el in query_apikey:
            try:
                if PasswordHasher().verify(el[2], key):
                    api_key = el
                    break
            except:
                continue

        if not api_key or api_key[6] < datetime.now():
            raise HTTPException(status_code=403, detail="Invalid API Key.")

        cursor.execute("""
            INSERT INTO API_Requests
            (api_key, method, endpoint, ip, port)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            api_key[0],
            request.method,
            request.url.path,
            request.client.host,
            request.client.port
        ))
        connection.commit()

        return {
            "user": api_key[1],
            "exp": api_key[6]
        }




async def search(search_term: str, term_query, count: int = 10, page: int = 1):
    search_term = search_term.lower()

    if len(term_query) <= (page - 1) * count:
        return [ ]

    res = [ ]
    contains = [ ]
    jaro_winkler = { }
    for el in term_query:
        term = el[1].lower()

        if term == search_term:
            res.insert(0, el[0])
        elif term.startswith(search_term):
            res.append(el[0])
        elif search_term in term:
            contains.append(el[0])
        else:
            jaro_winkler[el[0]] = get_jaro_distance(search_term, term, winkler=True)

    if len(res) + len(contains) < count * page:
        jaro_winkler = [ k for k, v in sorted(jaro_winkler.items(), key=lambda item: item[1]) ]
        jaro_winkler.reverse()
    else:
        jaro_winkler = [ ]

    results = (res + contains + jaro_winkler)[(page - 1) * count : page * count]

    return results
