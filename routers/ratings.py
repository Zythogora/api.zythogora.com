from config import connection, cursor, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

router = APIRouter()



class Rating(BaseModel):
    beer: int
    appearance: int
    smell: int
    taste: int
    aftertaste: int
    score: int
    serving: int
    aromas_malty: bool = None
    aromas_hoppy: bool = None
    aromas_yeasty: bool = None
    aromas_earthy: bool = None
    aromas_herbal: bool = None
    aromas_woody: bool = None
    aromas_citrus: bool = None
    aromas_redfruits: bool = None
    aromas_tropicalfruits: bool = None
    aromas_honey: bool = None
    aromas_nut: bool = None
    aromas_spices: bool = None
    aromas_caramel: bool = None
    aromas_chocolate: bool = None
    aromas_coffee: bool = None
    comment: str = None

@router.post("/ratings", tags=["ratings"])
async def add_rating(response: Response, rating: Rating, api_key : APIKey = Depends(get_api_key)):
    if rating.aromas_malty or rating.aromas_hoppy or rating.aromas_yeasty \
      or rating.aromas_earthy or rating.aromas_herbal or rating.aromas_woody \
      or rating.aromas_citrus or rating.aromas_redfruits or rating.aromas_tropicalfruits \
      or rating.aromas_honey or rating.aromas_nut or rating.aromas_spices \
      or rating.aromas_caramel or rating.aromas_chocolate or rating.aromas_coffee:
        if not rating.aromas_malty:
            rating.aromas_malty = False
        if not rating.aromas_hoppy:
            rating.aromas_hoppy = False
        if not rating.aromas_yeasty:
            rating.aromas_yeasty = False
        if not rating.aromas_earthy:
            rating.aromas_earthy = False
        if not rating.aromas_herbal:
            rating.aromas_herbal = False
        if not rating.aromas_woody:
            rating.aromas_woody = False
        if not rating.aromas_citrus:
            rating.aromas_citrus = False
        if not rating.aromas_redfruits:
            rating.aromas_redfruits = False
        if not rating.aromas_tropicalfruits:
            rating.aromas_tropicalfruits = False
        if not rating.aromas_honey:
            rating.aromas_honey = False
        if not rating.aromas_nut:
            rating.aromas_nut = False
        if not rating.aromas_spices:
            rating.aromas_spices = False
        if not rating.aromas_caramel:
            rating.aromas_caramel = False
        if not rating.aromas_chocolate:
            rating.aromas_chocolate = False
        if not rating.aromas_coffee:
            rating.aromas_coffee = False
    cursor.execute("""
        INSERT INTO Ratings (
            user, beer,
            appearance, smell, taste, aftertaste, score,
            serving,
            aromas_malty, aromas_hoppy, aromas_yeasty,
            aromas_earthy, aromas_herbal, aromas_woody,
            aromas_citrus, aromas_redfruits, aromas_tropicalfruits,
            aromas_honey, aromas_nut, aromas_spices,
            aromas_caramel, aromas_chocolate, aromas_coffee,
            comment
        ) VALUES (
            %s, %s,
            %s, %s, %s, %s, %s,
            %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s
        )
    """, (
        rating.beer,
        api_key["user"],
        rating.appearance, rating.smell, rating.taste, rating.aftertaste,
        rating.score,
        rating.serving,
        rating.aromas_malty, rating.aromas_hoppy, rating.aromas_yeasty,
        rating.aromas_earthy, rating.aromas_herbal, rating.aromas_woody,
        rating.aromas_citrus, rating.aromas_redfruits, rating.aromas_tropicalfruits,
        rating.aromas_honey, rating.aromas_nut, rating.aromas_spices,
        rating.aromas_caramel, rating.aromas_chocolate, rating.aromas_coffee,
        rating.comment
    ))
    connection.commit()
    rating_id = cursor.lastrowid

    cursor.execute("SELECT date FROM Ratings WHERE id=%s", (rating_id,))
    query_ratings = cursor.fetchone()

    return await get_rating(rating_id)



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
