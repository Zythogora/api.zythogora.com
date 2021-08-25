from config import connection, cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

router = APIRouter()



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

    return {
        "id": query_breweries[0],
        "name": query_breweries[1],
        "country": query_breweries[2]
    }


class Brewery(BaseModel):
    name: str
    country: int
    added_by: int

@router.post("/breweries", tags=["breweries"])
async def add_brewery(brewery: Brewery):
    cursor.execute("SELECT id FROM Breweries WHERE name=%s", (brewery.name, ))
    query_breweries = cursor.fetchone()
    if query_breweries:
        raise HTTPException(status_code=409, detail="This brewery already exists (" + str(query_breweries[0]) + ").")

    cursor.execute(
        "INSERT INTO Breweries " +
        "(name, country, added_by) " +
        "VALUES (%s, %s, %s)"
    , (
        brewery.name,
        brewery.country,
        brewery.added_by
    ))
    connection.commit()

    return {
        "id": cursor.lastrowid,
        "name": brewery.name,
        "country": brewery.country
    }
