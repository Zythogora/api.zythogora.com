from config import cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

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
