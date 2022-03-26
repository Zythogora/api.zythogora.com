from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

import routers.breweries as r_breweries
import routers.colors as r_colors
import routers.styles as r_styles
import routers.ratings as r_ratings

router = APIRouter()



class Beer(BaseModel):
    name: str
    brewery: int
    style: int
    abv: float
    ibu: int = None
    color: int = None

@router.post("/beers", tags=["beers"])
async def add_beer(response: Response, beer: Beer, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Beers
            WHERE name=%s AND brewery=%s
        """, (beer.name, beer.brewery ))
        query_beers = cursor.fetchone()

        if query_beers:
            beer_id = query_beers[0]
            response.status_code = status.HTTP_409_CONFLICT

        else:
            cursor.execute("""
                SELECT id
                FROM Breweries
                WHERE id=%s
            """, (rating.brewery, ))
            if not cursor.fetchone():
                raise HTTPException(status_code=422, detail="Brewery unknown")

            cursor.execute("""
                SELECT id
                FROM Styles
                WHERE id=%s
            """, (rating.style, ))
            if not cursor.fetchone():
                raise HTTPException(status_code=422, detail="Style unknown")

            if rating.abv < 0 or rating.abv > 100:
                raise HTTPException(status_code=422, detail="ABV value invalid")

            if rating.ibu < 0 or rating.ibu > 100:
                raise HTTPException(status_code=422, detail="IBU value invalid")

            cursor.execute("""
                SELECT id
                FROM Colors
                WHERE id=%s
            """, (rating.color, ))
            if not cursor.fetchone():
                raise HTTPException(status_code=422, detail="Color unknown")

            cursor.execute("""
                INSERT INTO Beers
                (name, brewery, style, abv, ibu, color, added_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                beer.name,
                beer.brewery,
                beer.style,
                beer.abv,
                beer.ibu,
                beer.color,
                api_key["user"]
            ))
            connection.commit()
            beer_id = cursor.lastrowid

        return await get_beer(beer_id, api_key)



@router.get("/beers/{beer_id}", tags=["beers"])
async def get_beer(beer_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name, brewery, style, abv, ibu, color
            FROM Beers
            WHERE id=%s
        """, (beer_id,))
        query_beers = cursor.fetchone()

        if not query_beers:
            raise HTTPException(status_code=404, detail="The beer you requested does not exist.")

        brewery = await r_breweries.get_brewery(query_beers[2], api_key)

        style = await r_styles.get_style(query_beers[3], api_key=api_key)

        if query_beers[6]:
            color = await r_colors.get_color(query_beers[6], api_key)
        else:
            color = None

        return {
            "id": query_beers[0],
            "name": query_beers[1],
            "brewery": brewery,
            "style": style,
            "abv": query_beers[4],
            "ibu": query_beers[5],
            "color": color
        }



@router.get("/beers/{beer_id}/ratings", tags=["beers"])
async def get_beer_ratings(beer_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id FROM Beers WHERE id=%s", (beer_id,))
        query_beers = cursor.fetchone()

        if not query_beers:
            raise HTTPException(status_code=404, detail="The beer you requested does not exist.")

        cursor.execute("""
            SELECT id FROM Ratings
            WHERE beer=%s
            ORDER BY date DESC
        """, (beer_id,))
        query_ratings = cursor.fetchall()

        res = [ ]
        for row in query_ratings:
            rating = await r_ratings.get_rating(row[0], api_key)
            res.append(rating)

        return res



@router.get("/beers/{beer_id}/averageScore", tags=["beers"])
async def get_beer_average_score(beer_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id FROM Beers WHERE id=%s", (beer_id,))
        query_beers = cursor.fetchone()

        if not query_beers:
            raise HTTPException(status_code=404, detail="The beer you requested does not exist.")

        cursor.execute("""
            SELECT AVG(score), COUNT(id) FROM Ratings
            WHERE beer=%s
        """, (beer_id,))
        query_ratings = cursor.fetchone()

        if not query_ratings or query_ratings[0] == None:
            raise HTTPException(status_code=404, detail="The beer you requested does not have any rating.")

        return {
            "id": beer_id,
            "averageScore": query_ratings[0],
            "reviews": query_ratings[1]
        }



@router.get("/beers/search/{beer_name}", tags=["beers"])
async def search_beer(beer_name: str, count: int = 10, page: int = 1, api_key: APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT Beers.id, Beers.name, SUM(Ratings.score) AS popularity FROM Beers
            LEFT JOIN Ratings ON Beers.id=Ratings.beer
            GROUP BY Ratings.beer ORDER BY popularity DESC
        """)
        query_beers = cursor.fetchall()

        beer_ids = await search(beer_name, query_beers, count, page)

        res = [ ]
        for i in beer_ids:
            data = await get_beer(i, api_key)
            res.append(data)

        return res
