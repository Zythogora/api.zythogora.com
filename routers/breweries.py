from config import cursor
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/breweries/{brewery_id}", tags=["breweries"])
async def get_brewery(brewery_id: int):
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
