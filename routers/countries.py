from config import connection, get_api_key, search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey

router = APIRouter()



@router.get("/countries/v2/{country_id}", tags=["countries_v2"])
async def get_country_v2(country_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name, code, flag, phone
            FROM Countries_v2
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



@router.get("/countries/v2", tags=["countries_v2"])
async def get_countries_v2(api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Countries_v2
            ORDER BY name
        """)
        query_countries = cursor.fetchall()

        res = [ ]
        for el in query_countries:
            data = await get_country_v2(el[0], api_key)
            res.append(data)

        return res



@router.get("/countries/{country_id}", tags=["countries"])
async def get_country(country_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name, flag
            FROM Countries
            WHERE id=%s
        """, (country_id,))
        query_countries = cursor.fetchone()

        if not query_countries:
            raise HTTPException(status_code=404, detail="The country you requested does not exist.")

        return {
            "id": query_countries[0],
            "name": query_countries[1],
            "flag": query_countries[2].strip()
        }



@router.get("/countries", tags=["countries"])
async def get_countries(api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Countries
            ORDER BY name
        """)
        query_countries = cursor.fetchall()

        res = [ ]
        for el in query_countries:
            data = await get_country(el[0], api_key)
            res.append(data)

        return res



@router.get("/countries/search/{country_name}", tags=["countries"])
async def search_country(country_name: str, count: int = 10, page: int = 1, api_key: APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("SELECT id, name FROM Countries")
        query_countries = cursor.fetchall()

        country_ids = await search(country_name, query_countries, count, page)

        res = [ ]
        for i in country_ids:
            data = await get_country(i, api_key)
            res.append(data)

        return res
