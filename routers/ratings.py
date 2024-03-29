from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

import routers.beers as r_beers
import routers.servings as r_servings
import routers.users as r_users

router = APIRouter()



class Rating(BaseModel):
    beer: int
    appearance: int
    smell: int
    taste: int
    aftertaste: int
    score: float
    serving: int
    comment: str = None

@router.post("/ratings", tags=["ratings"])
async def add_rating(response: Response, rating: Rating, api_key : APIKey = Depends(get_api_key)):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Beers
            WHERE id=%s
        """, (rating.beer, ))
        if not cursor.fetchone():
            raise HTTPException(status_code=422, detail="Beer unknown")

        if rating.score < 0 or rating.score > 10:
            raise HTTPException(status_code=422, detail="Score value invalid")

        # FIXME: add serving back
        # cursor.execute("""
        #     SELECT id
        #     FROM Servings
        #     WHERE id=%s
        # """, (rating.serving, ))
        # if not cursor.fetchone():
        #     raise HTTPException(status_code=422, detail="Serving unknown")

        cursor.execute("""
            INSERT INTO Ratings (
                user, beer,
                appearance, smell, taste, aftertaste, score,
                serving,
                comment
            ) VALUES (
                %s, %s,
                %s, %s, %s, %s, %s,
                %s,
                %s
            )
        """, (
            api_key["user"],
            rating.beer,
            rating.appearance, rating.smell, rating.taste, rating.aftertaste,
            rating.score,
            rating.serving,
            rating.comment
        ))
        connection.commit()
        rating_id = cursor.lastrowid

        cursor.execute("SELECT date FROM Ratings WHERE id=%s", (rating_id,))
        query_ratings = cursor.fetchone()

        return await get_rating(rating_id)



@router.get("/ratings/{rating_id}", tags=["ratings"])
async def get_rating(rating_id: int):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT
                id, user, beer,
                appearance, smell, taste, aftertaste, score, serving,
                comment, date
            FROM Ratings
            WHERE id=%s
        """, (rating_id,))
        query_ratings = cursor.fetchone()

        if not query_ratings:
            raise HTTPException(status_code=404, detail="The rating you requested does not exist.")

        user = await r_users.get_user(query_ratings[1])
        beer = await r_beers.get_beer(query_ratings[2])

        if query_ratings[8]:
            serving = await r_servings.get_serving(query_ratings[8])
        else:
            serving = None

        return {
            "id": query_ratings[0],
            "user": user,
            "beer": beer,
            "appearance": query_ratings[3],
            "smell": query_ratings[4],
            "taste": query_ratings[5],
            "aftertaste": query_ratings[6],
            "score": query_ratings[7],
            "serving": serving,
            "comment": query_ratings[9],
            "date": query_ratings[10]
        }
