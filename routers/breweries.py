from config import connection, cursor, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

from routers.countries import get_country

router = APIRouter()



class Brewery(BaseModel):
    name: str
    country: int

@router.post("/breweries", tags=["breweries"])
async def add_brewery(response: Response, brewery: Brewery, api_key : APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id FROM Breweries WHERE name=%s", (brewery.name, ))
    query_breweries = cursor.fetchone()

    if query_breweries:
        brewery_id = query_breweries[0]
        response.status_code = status.HTTP_409_CONFLICT

    else:
        cursor.execute(
            "INSERT INTO Breweries " +
            "(name, country, added_by) " +
            "VALUES (%s, %s, %s)"
        , (
            brewery.name,
            brewery.country,
            api_key["user"]
        ))
        connection.commit()
        brewery_id = cursor.lastrowid

    return await get_brewery(brewery_id, api_key)



@router.get("/breweries/{brewery_id}", tags=["breweries"])
async def get_brewery(brewery_id: int, api_key : APIKey = Depends(get_api_key)):
    cursor.execute(
        "SELECT id, name, country " +
        "FROM Breweries " +
        "WHERE id=%s"
    , (brewery_id,))
    query_breweries = cursor.fetchone()

    if not query_breweries:
        raise HTTPException(status_code=404, detail="The brewery you requested does not exist.")

    country = await get_country(query_breweries[2], api_key)

    return {
        "id": query_breweries[0],
        "name": query_breweries[1],
        "country": country
    }



@router.get("/breweries/search/{brewery_name}", tags=["breweries"])
async def search_brewery(brewery_name: str, count: int = 10, api_key: APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id, name FROM Breweries")
    query_breweries = cursor.fetchall()

    return await search(brewery_name, query_breweries, count)
