from config import cursor
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/styles/{style_id}", tags=["styles"])
async def get_style(style_id: int):
    cursor.execute(
        "SELECT Styles.id, Styles.name, SubStyles.id AS substyle_id, SubStyles.name AS substyle_name " +
        "FROM Styles " +
        "LEFT JOIN SubStyles ON SubStyles.style = Styles.id " +
        "WHERE Styles.id=%s " +
        "ORDER BY Styles.id"
    , (style_id,))
    query_styles = cursor.fetchall()

    if not query_styles:
        raise HTTPException(status_code=404, detail="The style you requested does not exist.")

    if cursor.rowcount == 1:
        return {
            "id": query_styles[0][0],
            "name": query_styles[0][1],
            "substyle_id": query_styles[0][2],
            "substyle_name": query_styles[0][3]
        }
    else:
        styles = []
        for row in query_styles:
            styles.append({
                "id": row[0],
                "name": row[1],
                "substyle_id": row[2],
                "substyle_name": row[3]
            })
        return styles

@router.get("/styles/{style_id}/{substyle_id}/", tags=["styles"])
async def get_style(style_id: int, substyle_id: int):
    cursor.execute(
        "SELECT Styles.id, Styles.name, SubStyles.id AS substyle_id, SubStyles.name AS substyle_name " +
        "FROM Styles " +
        "LEFT JOIN SubStyles ON SubStyles.style = Styles.id " +
        "WHERE Styles.id=%s AND SubStyles.id=%s " +
        "ORDER BY Styles.id"
    , (style_id, substyle_id,))
    query_styles = cursor.fetchone()

    if not query_styles:
        raise HTTPException(status_code=404, detail="The style you requested does not exist.")

    return {
        "id": query_styles[0],
        "name": query_styles[1],
        "substyle_id": query_styles[2],
        "substyle_name": query_styles[3]
    }

