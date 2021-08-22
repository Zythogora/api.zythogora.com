from config import cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

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
