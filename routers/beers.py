from config import connection, cursor, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

from routers.breweries import get_brewery
from routers.colors import get_color
from routers.styles import get_style, get_styles

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
async def add_beer(response: Response, beer: Beer, api_key : APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id FROM Beers WHERE name=%s AND brewery=%s", (beer.name, beer.brewery ))
    query_beers = cursor.fetchone()
    if query_beers:
        beer_id = query_beers[0]
        response.status_code = status.HTTP_409_CONFLICT

    else:
        if beer.substyle:
            cursor.execute(
                "INSERT INTO Beers " +
                "(name, brewery, style, sub_style, abv, ibu, color, added_by)" +
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
        beer_id = cursor.lastrowid

    return {
        "id": beer_id,
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

    brewery = await get_brewery(query_beers[2], api_key)

    if query_beers[4]:
        style = await get_style(query_beers[3], query_beers[4], api_key)
    else:
        style = (await get_styles(query_beers[3], api_key))[0]
        style["substyle"] = None

    if query_beers[7]:
        color = await get_color(query_beers[7], api_key)
    else:
        color = None

    return {
        "id": query_beers[0],
        "name": query_beers[1],
        "brewery": brewery,
        "style": style,
        "abv": query_beers[5],
        "ibu": query_beers[6],
        "color": color
    }



@router.get("/beers/search/{beer_name}", tags=["beers"])
async def search_beer(beer_name: str, count: int = 10, api_key: APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id, name FROM Beers")
    query_beers = cursor.fetchall()

    return await search(beer_name, query_beers, count)
