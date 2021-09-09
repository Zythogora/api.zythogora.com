from config import connection, cursor, get_api_key
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

router = APIRouter()



class Style(BaseModel):
    name: str
    substyle_name: str = None

@router.post("/styles", tags=["styles"])
async def add_style(response: Response, style: Style, api_key : APIKey = Depends(get_api_key)):
    style_id = None
    substyle_id = None

    cursor.execute("SELECT id FROM Styles WHERE name = %s", (style.name, ))
    query_styles = cursor.fetchone()

    if query_styles:
        style_id = query_styles[0]

        if style.substyle_name:
            cursor.execute(
                "SELECT SubStyles.id AS id FROM Styles " +
                "LEFT JOIN SubStyles ON Styles.id = SubStyles.style " +
                "WHERE Styles.name = %s AND SubStyles.name = %s"
            , (style.name, style.substyle_name))
            query_substyles = cursor.fetchone()

            if query_substyles:
                substyle_id = query_substyles[0]
                response.status_code = status.HTTP_409_CONFLICT

            else:
                cursor.execute(
                    "INSERT INTO SubStyles " +
                    "(name, style, added_by) " +
                    "VALUES (%s, %s, %s)"
                , (
                    style.substyle_name,
                    style_id,
                    api_key["user"]
                ))
                connection.commit()
                substyle_id = cursor.lastrowid

        else:
            response.status_code = status.HTTP_409_CONFLICT

    else:
        cursor.execute(
            "INSERT INTO Styles " +
            "(name, added_by) " +
            "VALUES (%s, %s)"
        , (
            style.name,
            api_key["user"]
        ))
        connection.commit()
        style_id = cursor.lastrowid

        if style.substyle_name:
            cursor.execute(
                "INSERT INTO SubStyles " +
                "(name, style, added_by) " +
                "VALUES (%s, %s, %s)"
            , (
                style.substyle_name,
                style_id,
                api_key["user"]
            ))
            connection.commit()
            substyle_id = cursor.lastrowid

    return {
        "id": style_id,
        "name": style.name,
        "substyle_id": substyle_id,
        "substyle_name": style.substyle_name
    }



@router.get("/styles/{style_id}", tags=["styles"])
async def get_style(style_id: int, api_key : APIKey = Depends(get_api_key)):
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
async def get_style(style_id: int, substyle_id: int, api_key : APIKey = Depends(get_api_key)):
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
