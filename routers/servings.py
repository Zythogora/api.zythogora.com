from config import connection, search
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/servings/{serving_id}", tags=["servings"])
async def get_serving(serving_id: int):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name
            FROM Servings
            WHERE id=%s
        """, (serving_id,))
        query_servings = cursor.fetchone()

        if not query_servings:
            raise HTTPException(status_code=404, detail="The serving type you requested does not exist.")

        return {
            "id": query_servings[0],
            "name": query_servings[1]
        }



@router.get("/servings", tags=["servings"])
async def get_servings():
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Servings
            ORDER BY name
        """)
        query_servings = cursor.fetchall()

        res = [ ]
        for el in query_servings:
            data = await get_serving(el[0])
            res.append(data)

        return res



@router.get("/servings/search/{serving_name}", tags=["servings"])
async def search_serving(serving_name: str, count: int = 10, page: int = 1):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id, name FROM Servings")
        query_servings = cursor.fetchall()

        serving_ids = await search(serving_name, query_servings, count, page)

        res = [ ]
        for i in serving_ids:
            data = await get_serving(i)
            res.append(data)

        return res
