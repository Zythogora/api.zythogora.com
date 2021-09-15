from config import cursor, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

router = APIRouter()



@router.get("/servings/{serving_id}", tags=["servings"])
async def get_serving(serving_id: int, api_key : APIKey = Depends(get_api_key)):
    cursor.execute(
        "SELECT id, name " +
        "FROM Servings " +
        "WHERE id=%s"
    , (serving_id,))
    query_servings = cursor.fetchone()

    if not query_servings:
        raise HTTPException(status_code=404, detail="The serving type you requested does not exist.")

    return {
        "id": query_servings[0],
        "name": query_servings[1]
    }



@router.get("/servings/search/{serving_name}", tags=["servings"])
async def search_serving(serving_name: str, count: int = 10, api_key: APIKey = Depends(get_api_key)):
    cursor.execute("SELECT id, name FROM Servings")
    query_servings = cursor.fetchall()

    return await search(serving_name, query_servings, count)
