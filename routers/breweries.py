from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

import routers.beers as r_beers
import routers.countries as r_countries

router = APIRouter()



class Brewery(BaseModel):
    name: str
    country: int

@router.post("/breweries", tags=["breweries"])
async def add_brewery(response: Response, brewery: Brewery, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id FROM Breweries WHERE name=%s", (brewery.name, ))
        query_breweries = cursor.fetchone()

        if query_breweries:
            brewery_id = query_breweries[0]
            response.status_code = status.HTTP_409_CONFLICT

        else:
            cursor.execute("""
                INSERT INTO Breweries
                (name, country, added_by)
                VALUES (%s, %s, %s)
            """, (
                brewery.name,
                brewery.country,
                api_key["user"]
            ))
            connection.commit()
            brewery_id = cursor.lastrowid

        return await get_brewery(brewery_id, api_key)



@router.get("/breweries/{brewery_id}", tags=["breweries"])
async def get_brewery(brewery_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name, country
            FROM Breweries
            WHERE id=%s
        """, (brewery_id,))
        query_breweries = cursor.fetchone()

        if not query_breweries:
            raise HTTPException(status_code=404, detail="The brewery you requested does not exist.")

        country = await r_countries.get_country(query_breweries[2], api_key)

        return {
            "id": query_breweries[0],
            "name": query_breweries[1],
            "country": country
        }



@router.get("/breweries/{brewery_id}/beers", tags=["breweries"])
async def get_brewery_beers(brewery_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Beers
            WHERE brewery=%s
            ORDER BY name ASC
        """, (brewery_id,))
        query_beers = cursor.fetchall()

        res = [ ]
        for el in query_beers:
            beer = await r_beers.get_beer(el[0], api_key)
            res.append(beer)
        return res



@router.get("/breweries/search/{brewery_name}", tags=["breweries"])
async def search_brewery(brewery_name: str, count: int = 10, page: int = 1, api_key: APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT Breweries.id, Breweries.name, SUM(Sub.popularity) AS popularity FROM (
                SELECT Beers.id, Beers.brewery, SUM(Ratings.score) AS popularity FROM Beers
                LEFT JOIN Ratings ON Beers.id = Ratings.beer
                GROUP BY Ratings.beer
            ) AS Sub
            LEFT JOIN Breweries ON Breweries.id = Sub.brewery
            GROUP BY Breweries.id ORDER BY popularity DESC
        """)
        query_breweries = cursor.fetchall()

        brewery_ids = await search(brewery_name, query_breweries, count, page)

        res = [ ]
        for i in brewery_ids:
            data = await get_brewery(i, api_key)
            res.append(data)

        return res
