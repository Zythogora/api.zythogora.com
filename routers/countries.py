from config import connection, search
from fastapi import APIRouter, HTTPException

router = APIRouter()



@router.get("/countries/{country_id}", tags=["countries"])
async def get_country(country_id: int):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name, code, flag, phone
            FROM Countries
            WHERE id=%s
        """, (country_id,))
        query_countries = cursor.fetchone()

        if not query_countries:
            raise HTTPException(status_code=404, detail="The country you requested does not exist.")

        return {
            "id": query_countries[0],
            "name": query_countries[1],
            "code": query_countries[2],
            "flag": query_countries[3],
            "phone": query_countries[4],
        }



@router.get("/countries", tags=["countries"])
async def get_countries():
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Countries
            ORDER BY name
        """)
        query_countries = cursor.fetchall()

        res = [ ]
        for el in query_countries:
            data = await get_country(el[0])
            res.append(data)

        return res



@router.get("/countries/search/{country_name}", tags=["countries"])
async def search_country(country_name: str, count: int = 10, page: int = 1):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id, name FROM Countries")
        query_countries = cursor.fetchall()

        country_ids = await search(country_name, query_countries, count, page)

        res = [ ]
        for i in country_ids:
            data = await get_country(i)
            res.append(data)

        return res
