from config import cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

router = APIRouter()



@router.get("/users/{user_id}", tags=["users"])
async def get_user(user_id: int, api_key : APIKey = Depends(get_api_key)):
    cursor.execute(
        "SELECT Users.id, Users.username, Users.nationality, COUNT(Ratings.id) AS ratings " +
        "FROM Ratings " +
        "JOIN Users ON Ratings.user = Users.id " +
        "WHERE Users.id = %s"
    , (user_id,))
    query_users = cursor.fetchone()

    if not query_users:
        raise HTTPException(status_code=404, detail="The user you requested does not exist.")

    return {
        "id": query_users[0],
        "username": query_users[1],
        "nationality": query_users[2],
        "ratings": query_users[3]
    }
