from config import cursor
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/countries/{country_id}", tags=["countries"])
async def get_country(country_id: int):
    cursor.execute(
        "SELECT id, name, flag " +
        "FROM Countries " +
        "WHERE id=%s"
    , (country_id,))
    query_countries = cursor.fetchone()

    if not query_countries:
        raise HTTPException(status_code=404, detail="The country you requested does not exist.")

    return {
        "id": query_countries[0],
        "name": query_countries[1],
        "flag": query_countries[2].strip()
    }

