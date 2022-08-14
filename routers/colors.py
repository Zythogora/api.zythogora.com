from config import connection, search
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/colors/{color_id}", tags=["colors"])
async def get_color(color_id: int):
    with connection.cursor(prepared=True) as cursor:
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
async def get_colors():
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Colors
        """)
        query_colors = cursor.fetchall()

        res = [ ]
        for el in query_colors:
            data = await get_color(el[0])
            res.append(data)

        return res



@router.get("/colors/search/{color_name}", tags=["colors"])
async def search_color(color_name: str, count: int = 10, page: int = 1):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id, name FROM Colors")
        query_colors = cursor.fetchall()

        color_ids = await search(color_name, query_colors, count, page)

        res = [ ]
        for i in color_ids:
            data = await get_color(i)
            res.append(data)

        return res
