from config import connection, cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel
from pyjarowinkler.distance import get_jaro_distance

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



@router.get("/beers/search/{beer_name}", tags=["beers"])
async def search_beer(beer_name: str, count: int = 10, api_key: APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id, name FROM Beers")
    query_beers = cursor.fetchall()

    beer_name = beer_name.lower()

    res = [ ]
    contains = [ ]
    jaro_winkler = { }
    for row in query_beers:
        name = row[1].lower()
        if name.startswith(beer_name):
            res.append(row[0])

            if len(res) == count:
                return res

        elif beer_name in name:
            contains.append(row[0])

        else:
            jaro_winkler[row[0]] = get_jaro_distance(row[1], beer_name, winkler=True)

    if len(res) + len(contains) >= count:
        return res + contains[:(count - len(res))]

    jaro_winkler = [ k for k, v in sorted(jaro_winkler.items(), key=lambda item: item[1]) ]
    jaro_winkler.reverse()

    return res + contains[:(count - len(res))] + jaro_winkler[:(count - len(res) - len(contains))]
