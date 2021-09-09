from config import connection, cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

router = APIRouter()



class Beer(BaseModel):
    name: str
    brewery: int
    style: int
    substyle: int = None
    abv: float
    ibu: int
    color: int

@router.post("/beers", tags=["beers"])
async def add_beer(beer: Beer, api_key : APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id FROM Beers WHERE name=%s AND brewery=%s", (beer.name, beer.brewery ))
    query_beers = cursor.fetchone()
    if query_beers:
        raise HTTPException(status_code=409, detail="This beer already exists (" + str(query_beers[0]) + ").")

    if beer.substyle:
        cursor.execute(
            "INSERT INTO Beers " +
            "(name, brewery, style, substyle, abv, ibu, color, added_by)" +
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        , (
            beer.name,
            beer.brewery,
            beer.style,
            beer.substyle,
            beer.abv,
            beer.ibu,
            beer.color,
            api_key["user"]
        ))
    else:
        cursor.execute(
            "INSERT INTO Beers " +
            "(name, brewery, style, abv, ibu, color, added_by)" +
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        , (
            beer.name,
            beer.brewery,
            beer.style,
            beer.abv,
            beer.ibu,
            beer.color,
            api_key["user"]
        ))
    connection.commit()

    return {
        "id": cursor.lastrowid,
        "name": beer.name,
        "beer": beer.brewery,
        "style": beer.style,
        "substyle": beer.substyle,
        "abv": beer.abv,
        "ibu": beer.ibu,
        "color": beer.color
    }



@router.get("/beers/{beer_id}", tags=["beers"])
async def get_beer(beer_id: int, api_key : APIKey = Depends(get_api_key)):
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


