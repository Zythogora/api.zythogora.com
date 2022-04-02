from argon2 import PasswordHasher
from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
import jwt
import os
from pydantic import BaseModel
import time
import re

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
            raise HTTPException(status_code=401, detail="Invalid credentials")

        try:
            PasswordHasher().verify(query_users[2], login.password)
        except:
            raise HTTPException(status_code=401, detail="Invalid credentials")

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
            WHERE username=%s
        """, (register.username, ))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Username already in use")

        username_pattern = re.compile("^[a-zA-Z0-9_]+$")
        if username_pattern.match(register.username) is None:
            raise HTTPException(status_code=422, detail="Username contains forbidden characters")

        cursor.execute("""
            SELECT id
            FROM Users
            WHERE email=%s
        """, (register.email, ))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Email already in use")

        email_pattern = re.compile("^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$")
        if email_pattern.match(register.email) is None:
            raise HTTPException(status_code=422, detail="Email format unknown")

        password_pattern = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])(?=.{8,})")
        if password_pattern.match(register.password) is None:
            raise HTTPException(status_code=422, detail="Password is not strong enough")

        cursor.execute("""
            SELECT id
            FROM Countries
            WHERE id=%s
        """, (register.nationality, ))
        if not cursor.fetchone():
            raise HTTPException(status_code=422, detail="Country unknown")

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



@router.get("/users/{user}", tags=["users"])
async def get_user(user: str, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT Users.uuid, Users.username, Users.nationality, COUNT(Ratings.id) AS ratings
                FROM Ratings
                JOIN Users ON Ratings.user=Users.uuid
                WHERE Users.uuid=%s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT Users.uuid, Users.username, Users.nationality, COUNT(Ratings.id) AS ratings
                FROM Ratings
                JOIN Users ON Ratings.user=Users.uuid
                WHERE Users.username=%s
            """, (user, ))
        query_users = cursor.fetchone()

        if not query_users or not query_users[0]:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        return {
            "id": query_users[0],
            "username": query_users[1],
            "nationality": query_users[2],
            "ratings": query_users[3]
        }



@router.get("/users/{user}/ratings", tags=["users"])
async def get_user_ratings(user: str, count: int = 10, page: int = 1, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE uuid=%s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE username=%s
            """, (user, ))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        cursor.execute("""
            SELECT id
            FROM Ratings
            WHERE user=%s
            ORDER BY date DESC
            LIMIT %s, %s
        """, (query_users[0], (page - 1) * count, count))
        query_ratings = cursor.fetchall()

        res = [ ]
        for row in query_ratings:
            rating = await r_ratings.get_rating(row[0], api_key)
            res.append(rating)

        return res



@router.get("/users/{user}/ratings/since/{date}", tags=["users"])
async def get_user_ratings_since(user: str, date: str, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE uuid=%s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE username=%s
            """, (user, ))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        if not date[-1] in [ "H", "D", "W", "M", "Y" ]:
            raise HTTPException(status_code=422, detail="Unknown date type. Supported types are H (hours), D (days), W (weeks), M (months) and Y (years).")

        date_type = { "H": "HOUR", "D": "DAY", "W": "WEEK", "M": "MONTH", "Y": "YEAR" }[date[-1]]

        if not date[:-1].isnumeric():
            raise HTTPException(status_code=422, detail="The duration must be a number.")

        date_interval = int(date[:-1])
        if date_interval <= 0:
            raise HTTPException(status_code=422, detail="Invalid duration.")
        
        print(date_type, date_interval)

        cursor.execute(f"""
            SELECT id
            FROM Ratings
            WHERE
                user=%s AND
                date BETWEEN
                    DATE_SUB(NOW(), INTERVAL {date_interval} {date_type})
                    AND NOW()
            ORDER BY date DESC
        """, (query_users[0], ))
        query_ratings = cursor.fetchall()

        res = [ ]
        for row in query_ratings:
            rating = await r_ratings.get_rating(row[0], api_key)
            res.append(rating)

        return res



@router.get("/users/search/{username}", tags=["users"])
async def search_user(username: str, count: int = 10, page: int = 1, api_key: APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT uuid, username
            FROM Users
        """)
        query_users = cursor.fetchall()

        user_ids = await search(username, query_users, count, page)

        res = [ ]
        for i in user_ids:
            data = await get_user(i, api_key)
            res.append(data)

        return res
