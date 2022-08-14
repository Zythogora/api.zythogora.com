from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security.api_key import APIKey
from pydantic import BaseModel

router = APIRouter()



class Style(BaseModel):
    name: str
    substyle_name: str = None

@router.post("/styles", tags=["styles"])
async def add_style(response: Response, style: Style, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
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
                    substyle = {
                        "id": query_substyles[0],
                        "name": style.substyle_name
                    }
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
                    substyle = {
                        "id": cursor.lastrowid,
                        "name": style.substyle_name
                    }

            else:
                substyle = None
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
                substyle = {
                    "id": cursor.lastrowid,
                    "name": style.substyle_name
                }
            else:
                substyle = None

        return {
            "id": style_id,
            "name": style.name,
            "substyle": substyle
        }



@router.get("/styles/{style_id}", tags=["styles"])
async def get_style(style_id: int, depth: int = -1):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name, parent
            FROM Styles
            WHERE id=%s
        """, (style_id, ))
        query_styles = cursor.fetchone()

        if not query_styles:
            raise HTTPException(status_code=404, detail="The style you requested does not exist.")

        parent = None
        if depth != 0:
            if len(query_styles) > 2 and query_styles[2]:
                parent = await get_style(query_styles[2], depth - 1)

        return {
            "id": query_styles[0],
            "name": query_styles[1],
            "parent": parent
        }



@router.get("/styles", tags=["styles"])
async def get_styles():
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Styles
            ORDER BY name
        """)
        query_styles = cursor.fetchall()

        res = [ ]
        for el in query_styles:
            data = await get_style(el[0])
            res.append(data)

        return res



@router.get("/styles/search/{style_name}", tags=["styles"])
async def search_style(style_name: str, count: int = 10, page: int = 1):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id, name FROM Styles")
        query_styles = cursor.fetchall()

        style_ids = await search(style_name, query_styles, count, page)

        res = [ ]
        for i in style_ids:
            data = await get_style(i)
            res.append(data)

        return res
