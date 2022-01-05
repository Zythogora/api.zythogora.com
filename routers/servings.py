from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

router = APIRouter()



@router.get("/servings/{serving_id}", tags=["servings"])
async def get_serving(serving_id: int, api_key : APIKey = Depends(get_api_key)):
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
async def get_servings(api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Servings
            ORDER BY name
        """)
        query_servings = cursor.fetchall()

        if not query_servings:
            raise HTTPException(status_code=404, detail="The serving type you requested does not exist.")

        res = [ ]
        for el in query_servings:
            data = await get_serving(el[0], api_key)
            res.append(data)

        return res



@router.get("/servings/search/{serving_name}", tags=["servings"])
async def search_serving(serving_name: str, count: int = 10, page: int = 1, api_key: APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id, name FROM Servings")
        query_servings = cursor.fetchall()

        serving_ids = await search(serving_name, query_servings, count, page)

        res = [ ]
        for i in serving_ids:
            data = await get_serving(i, api_key)
            res.append(data)

        return res
