from config import cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

router = APIRouter()



@router.get("/ratings/{rating_id}", tags=["ratings"])
async def get_rating(rating_id: int, api_key : APIKey = Depends(get_api_key)):
    cursor.execute(
        "SELECT id, user, beer, " + 
            "appearance, smell, taste, aftertaste, score, serving, " +
            "aromas_malty, aromas_hoppy, aromas_yeasty, " +
            "aromas_earthy, aromas_herbal, aromas_woody, " +
            "aromas_citrus, aromas_redfruits, aromas_tropicalfruits, " +
            "aromas_honey, aromas_nut, aromas_spices, " +
            "aromas_caramel, aromas_chocolate, aromas_coffee, " +
            "comment, date " +
        "FROM Ratings " +
        "WHERE id=%s"
    , (rating_id,))
    query_ratings = cursor.fetchone()

    if not query_ratings:
        raise HTTPException(status_code=404, detail="The rating you requested does not exist.")

    return {
        "id": query_ratings[0],
        "user": query_ratings[1],
        "beer": query_ratings[2],
        "appearance": query_ratings[3],
        "smell": query_ratings[4],
        "taste": query_ratings[5],
        "aftertaste": query_ratings[7],
        "score": query_ratings[7],
        "serving": query_ratings[8],
        "aromas_malty": query_ratings[9],
        "aromas_hoppy": query_ratings[10],
        "aromas_yeasty": query_ratings[11],
        "aromas_earthy": query_ratings[12],
        "aromas_herbal": query_ratings[13],
        "aromas_woody": query_ratings[14],
        "aromas_citrus": query_ratings[15],
        "aromas_redfruits": query_ratings[16],
        "aromas_tropicalfruits": query_ratings[17],
        "aromas_honey": query_ratings[18],
        "aromas_nut": query_ratings[19],
        "aromas_spices": query_ratings[20],
        "aromas_caramel": query_ratings[21],
        "aromas_chocolate": query_ratings[22],
        "aromas_coffee": query_ratings[23],
        "comment": query_ratings[24],
        "date": query_ratings[25]
    }
