from argon2 import PasswordHasher
from config import connection, search
from fastapi import APIRouter, HTTPException

import routers.ratings as r_ratings

router = APIRouter()



@router.get("/users/{user}", tags=["users"])
async def get_user(user: str):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT uuid, username, nationality
                FROM Users
                WHERE uuid = %s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT uuid, username, nationality
                FROM Users
                WHERE username = %s
            """, (user, ))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        cursor.execute("""
            SELECT COUNT(DISTINCT beer)
            FROM Ratings
            WHERE user = %s
        """, (query_users[0], ))
        query_beers = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(id)
            FROM Ratings
            WHERE user = %s
        """, (query_users[0], ))
        query_ratings = cursor.fetchone()

        return {
            "id": query_users[0],
            "username": query_users[1],
            "nationality": query_users[2],
            "beers": query_beers[0],
            "ratings": query_ratings[0]
        }



@router.get("/users/{user}/ratings", tags=["users"])
async def get_user_ratings(user: str, count: int = 10, page: int = 1):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE uuid = %s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE username = %s
            """, (user, ))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=404, detail="The user you requested does not exist.")

        cursor.execute("""
            SELECT id
            FROM Ratings
            WHERE user = %s
            ORDER BY date DESC
            LIMIT %s, %s
        """, (query_users[0], (page - 1) * count, count))
        query_ratings = cursor.fetchall()

        res = [ ]
        for row in query_ratings:
            rating = await r_ratings.get_rating(row[0])
            res.append(rating)

        return res



@router.get("/users/{user}/ratings/since/{date}", tags=["users"])
async def get_user_ratings_since(user: str, date: str):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        if "-" in user:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE uuid = %s
            """, (user, ))
        else:
            cursor.execute("""
                SELECT uuid
                FROM Users
                WHERE username = %s
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
                user = %s AND
                date BETWEEN
                    DATE_SUB(NOW(), INTERVAL {date_interval} {date_type})
                    AND NOW()
            ORDER BY date DESC
        """, (query_users[0], ))
        query_ratings = cursor.fetchall()

        res = [ ]
        for row in query_ratings:
            rating = await r_ratings.get_rating(row[0])
            res.append(rating)

        return res



@router.get("/users/search/{username}", tags=["users"])
async def search_user(username: str, count: int = 10, page: int = 1):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT uuid, username
            FROM Users
        """)
        query_users = cursor.fetchall()

        user_ids = await search(username, query_users, count, page)

        res = [ ]
        for i in user_ids:
            data = await get_user(i)
            res.append(data)

        return res
