from config import cursor
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/beers/{beer_id}", tags=["beers"])
async def get_beer(beer_id: int):
    cursor.execute(
        "SELECT id, name, brewery, style, sub_style, abv, ibu, color " +
        "FROM Beers " +
        "WHERE Beers.id = %s"
    , (beer_id,))
    query_beers = cursor.fetchone()

    if not query_beers:
        raise HTTPException(status_code=404, detail="The beer you requested does not exist.")

    return {
        "id": query_beers[0],
        "name": query_beers[1],
        "brewery": query_beers[2],
        "style": query_beers[3],
        "substyle": query_beers[4],
        "abv": query_beers[5],
        "ibu": query_beers[6],
        "color": query_beers[7]
    }

