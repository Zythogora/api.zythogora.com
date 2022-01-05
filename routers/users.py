from argon2 import PasswordHasher
from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
import jwt
import os
from pydantic import BaseModel
import time

import routers.ratings as r_ratings

router = APIRouter()



class Login(BaseModel):
    username: str
    password: str

@router.post("/users/login", tags=["users"])
async def login(login: Login, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT uuid, username, password_hash
            FROM Users
            WHERE username=%s
        """, (login.username,))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            PasswordHasher().verify(query_users[2], login.password)
        except:
            raise HTTPException(status_code=401, detail="Unauthorized")

        now = int(time.time())
        token = jwt.encode(
            {
                "client_id": query_users[0],
                "nickname": query_users[1],
                "iat": now,
                "exp": now + 60 * 60 * 24 * 7 * 6,
            }, os.environ["zythogora_jwt_secret"], algorithm="HS512")

        return { "token": token }



class Register(BaseModel):
    firstname: str
    lastname: str
    email: str
    username: str
    password: str
    nationality: int

@router.post("/users/register", tags=["users"])
async def register(register: Register, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Users
            WHERE username=%s OR email=%s
        """, (register.username, register.email))
        query_users = cursor.fetchone()

        if query_users:
            raise HTTPException(status_code=409, detail="This username / email is already in use")

        cursor.execute("""
            INSERT INTO Users
            (firstname, lastname, username, email, password_hash, nationality)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            register.firstname,
            register.lastname,
            register.username,
            register.email,
            PasswordHasher().hash(register.password),
            register.nationality
        ))
        connection.commit()

        cursor.execute("SELECT uuid FROM Users WHERE id=%s", (cursor.lastrowid, ))
        query_users = cursor.fetchone()

        now = int(time.time())
        token = jwt.encode(
            {
                "client_id": query_users[0],
                "nickname": register.username,
                "iat": now,
                "exp": now + 60 * 60 * 3,
            }, os.environ["zythogora_jwt_secret"], algorithm="HS512")

        return { "token": token }



@router.get("/users/{user_uuid}", tags=["users"])
async def get_user(user_uuid: str, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT Users.uuid, Users.username, Users.nationality, COUNT(Ratings.id) AS ratings
            FROM Ratings
            JOIN Users ON Ratings.user=Users.uuid
            WHERE Users.uuid=%s
        """, (user_uuid,))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        return {
            "id": query_users[0],
            "username": query_users[1],
            "nationality": query_users[2],
            "ratings": query_users[3]
        }



@router.get("/users/{user_uuid}/ratings", tags=["users"])
async def get_user_ratings(user_uuid: str, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT uuid FROM Users WHERE uuid=%s", (user_uuid,))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        cursor.execute("""
            SELECT id FROM Ratings
            WHERE user=%s
            ORDER BY date DESC
        """, (user_uuid,))
        query_ratings = cursor.fetchall()

        res = [ ]
        for row in query_ratings:
            rating = await r_ratings.get_rating(row[0], api_key)
            res.append(rating)

        return res



@router.get("/users/search/{username}", tags=["users"])
async def search_user(username: str, count: int = 10, page: int = 1, api_key: APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT uuid, username FROM Users")
        query_users = cursor.fetchall()

        user_ids = await search(username, query_users, count, page)

        res = [ ]
        for i in user_ids:
            data = await get_user(i, api_key)
            res.append(data)

        return res
