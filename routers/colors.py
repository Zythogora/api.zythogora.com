from config import cursor, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

router = APIRouter()



@router.get("/colors/{color_id}", tags=["colors"])
async def get_color(color_id: int, api_key : APIKey = Depends(get_api_key)):
    cursor.execute("""
        SELECT id, name, color
        FROM Colors
        WHERE id=%s
    """, (color_id,))
    query_colors = cursor.fetchone()

    if not query_colors:
        raise HTTPException(status_code=404, detail="The color you requested does not exist.")

    return {
        "id": query_colors[0],
        "name": query_colors[1],
        "color": query_colors[2]
    }



@router.get("/colors", tags=["colors"])
async def get_colors(api_key : APIKey = Depends(get_api_key)):
    cursor.execute("""
        SELECT id
        FROM Colors
        ORDER BY name
    """)
    query_colors = cursor.fetchall()

    if not query_colors:
        raise HTTPException(status_code=404, detail="The color you requested does not exist.")

    res = [ ]
    for el in query_colors:
        data = await get_color(el[0], api_key)
        res.append(data)

    return res



@router.get("/colors/search/{color_name}", tags=["colors"])
async def search_color(color_name: str, count: int = 10, api_key: APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id, name FROM Colors")
    query_colors = cursor.fetchall()

    color_ids = await search(color_name, query_colors, count)

    res = [ ]
    for i in color_ids:
        data = await get_color(i, api_key)
        res.append(data)

    return res
