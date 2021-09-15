from config import cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
from pyjarowinkler.distance import get_jaro_distance

router = APIRouter()



@router.get("/colors/{color_id}", tags=["colors"])
async def get_color(color_id: int, api_key : APIKey = Depends(get_api_key)):
    cursor.execute(
        "SELECT id, name, color " +
        "FROM Colors " +
        "WHERE id=%s"
    , (color_id,))
    query_colors = cursor.fetchone()

    if not query_colors:
        raise HTTPException(status_code=404, detail="The color you requested does not exist.")

    return {
        "id": query_colors[0],
        "name": query_colors[1],
        "color": query_colors[2]
    }



@router.get("/colors/search/{color_name}", tags=["colors"])
async def search_beer(color_name: str, count: int = 10, api_key: APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id, name FROM Colors")
    query_colors = cursor.fetchall()

    color_name = color_name.lower()

    res = [ ]
    contains = [ ]
    jaro_winkler = { }
    for row in query_colors:
        name = row[1].lower()
        if name.startswith(color_name):
            res.append(row[0])

            if len(res) == count:
                return res

        elif color_name in name:
            contains.append(row[0])

        else:
            jaro_winkler[row[0]] = get_jaro_distance(row[1], color_name, winkler=True)

    if len(res) + len(contains) >= count:
        return res + contains[:(count - len(res))]

    jaro_winkler = [ k for k, v in sorted(jaro_winkler.items(), key=lambda item: item[1]) ]
    jaro_winkler.reverse()

    return res + contains[:(count - len(res))] + jaro_winkler[:(count - len(res) - len(contains))]
