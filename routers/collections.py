from config import connection, get_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.api_key import APIKey
from pydantic import BaseModel
from typing import Union

import routers.beers as r_beers
import routers.users as r_users

router = APIRouter()



class Collection(BaseModel):
    name: str
    is_public: bool

@router.post("/collections", tags=["collections"])
async def add_collection(collection: Collection, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            INSERT INTO Collections
            (name, owner, is_public)
            VALUES (%s, %s, %s)
        """, (
            collection.name,
            api_key["user"],
            collection.is_public
        ))
        connection.commit()
        collection_id = cursor.lastrowid

    return await get_collection(collection_id, api_key)



@router.get("/collections/{collection_id}", tags=["collections"])
async def get_collection(collection_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, name, first, last, owner, is_public, creation_date, last_modification
            FROM Collections
            WHERE id = %s
        """, (collection_id,))
        query_collection = cursor.fetchone()

        if not query_collection:
            raise HTTPException(status_code=404, detail="The collection you requested does not exist.")

        if not query_collection[5] and api_key["user"] != query_collection[4]:
            raise HTTPException(status_code=403, detail="The collection you requested is private.")

        owner = await r_users.get_user(query_collection[4])

        cursor.execute("""
            SELECT id, beer, next, add_time
            FROM Collection_Items
            WHERE collection = %s
        """, (collection_id,))
        query_items = cursor.fetchall()

        items_data = {}
        for row in query_items:
            beer = await r_beers.get_beer(row[1])
            items_data[row[0]] = {
                "id": row[0],
                "beer": beer,
                "next": row[2],
                "add_time": row[3]
            }

        items = []
        current_beer = query_collection[2]
        while current_beer:
            current_beer_data = items_data[current_beer]
            items.append({
                "beer": current_beer_data["beer"],
                "add_time": current_beer_data["add_time"]
            })
            current_beer = current_beer_data["next"]

        return {
            "id": query_collection[0],
            "name": query_collection[1],
            "items": items,
            "owner": owner,
            "is_public": True if query_collection[5] else False,
            "creation_date": query_collection[6],
            "last_modification": query_collection[7]
        }



@router.patch("/collections/{collection_id}", tags=["collections"])
async def edit_collection(collection_id: int, collection: Collection, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, owner
            FROM Collections
            WHERE id = %s
        """, (collection_id,))
        query_collection = cursor.fetchone()

        if not query_collection:
            raise HTTPException(status_code=404, detail="The collection you want to edit does not exist.")

        if api_key["user"] != query_collection[1]:
            raise HTTPException(status_code=403, detail="The collection you want to edit does not belong to you.")

        cursor.execute("""
            UPDATE Collections
            SET name = %s, is_public = %s
            WHERE id = %s
        """, (collection.name, collection.is_public, collection_id))
        connection.commit()

    return await get_collection(collection_id, api_key)



@router.delete("/collections/{collection_id}", tags=["collections"])
async def delete_collection(collection_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, first, last, owner
            FROM Collections
            WHERE id = %s
        """, (collection_id,))
        query_collection = cursor.fetchone()

        if not query_collection:
            raise HTTPException(status_code=404, detail="The collection you want to delete does not exist.")

        if api_key["user"] != query_collection[3]:
            raise HTTPException(status_code=403, detail="The collection you want to delete does not belong to you.")

        if query_collection[1] or query_collection[2]:
            cursor.execute("""
                UPDATE Collections
                SET first = NULL, last = NULL
                WHERE id = %s
            """, (collection_id,))

            cursor.execute("""
                UPDATE Collection_Items
                SET previous = NULL, next = NULL
                WHERE collection = %s
            """, (collection_id,))

            cursor.execute("""
                DELETE FROM Collection_Items
                WHERE collection = %s
            """, (collection_id,))

        cursor.execute("""
            DELETE FROM Collections
            WHERE id = %s
        """, (collection_id,))

        connection.commit()

    return {
        "status": "Collection deleted"
    }



@router.post("/collections/{collection_id}/{beer_id}", tags=["collections"])
async def add_collection_item(collection_id: int, beer_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, first, last, owner
            FROM Collections
            WHERE id = %s
        """, (collection_id,))
        query_collection = cursor.fetchone()

        if not query_collection:
            raise HTTPException(status_code=404, detail="The collection you want to edit does not exist.")

        if api_key["user"] != query_collection[3]:
            raise HTTPException(status_code=403, detail="The collection you want to edit does not belong to you.")

        cursor.execute("""
            SELECT id
            FROM Beers
            WHERE id = %s
        """, (beer_id,))
        query_beer = cursor.fetchone()

        if not query_beer:
            raise HTTPException(status_code=404, detail="The beer you want to add does not exist.")

        cursor.execute("""
            INSERT INTO Collection_Items
            (beer, collection, previous)
            VALUES (%s, %s, %s)
        """, (
            beer_id,
            collection_id,
            query_collection[2]
        ))
        connection.commit()
        item_id = cursor.lastrowid

        cursor.execute("""
            UPDATE Collection_Items
            SET next = %s
            WHERE id = %s
        """, (item_id, query_collection[2]))

        if not query_collection[1]:
            cursor.execute("""
                UPDATE Collections
                SET first = %s, last = %s
                WHERE id = %s
            """, (item_id, item_id, collection_id))
        else:
            cursor.execute("""
                UPDATE Collections
                SET last = %s
                WHERE id = %s
            """, (item_id, collection_id))

        connection.commit()

    return await get_collection(collection_id, api_key)



class CollectionItem(BaseModel):
    previous: Union[int, None]
    next: Union[int, None]

@router.patch("/collections/{collection_id}/{beer_id}", tags=["collections"])
async def move_collection_item(collection_id: int, beer_id: int, item: CollectionItem, api_key : APIKey = Depends(get_api_key)):
    if item.previous == beer_id or item.next == beer_id:
        raise HTTPException(status_code=400, detail="The request body is invalid. (0)")

    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, first, last, owner
            FROM Collections
            WHERE id = %s
        """, (collection_id,))
        query_collection = cursor.fetchone()

        if not query_collection:
            raise HTTPException(status_code=404, detail="The collection you want to edit does not exist.")

        if api_key["user"] != query_collection[3]:
            raise HTTPException(status_code=403, detail="The collection you want to edit does not belong to you.")

        cursor.execute("""
            SELECT id, previous, next
            FROM Collection_Items
            WHERE beer = %s AND collection = %s
        """, (beer_id, collection_id))
        query_item = cursor.fetchone()

        if not query_item:
            raise HTTPException(status_code=404, detail="The item you want to edit does not exist.")

        if item.previous != None:
            cursor.execute("""
                SELECT id, previous, next
                FROM Collection_Items
                WHERE beer = %s AND collection = %s
            """, (item.previous, collection_id))
            query_previous = cursor.fetchone()

            if not query_previous:
                raise HTTPException(status_code=400, detail="The request body is invalid. (1a)")

        if item.next != None:
            cursor.execute("""
                SELECT id, previous, next
                FROM Collection_Items
                WHERE beer = %s AND collection = %s
            """, (item.next, collection_id))
            query_next = cursor.fetchone()

            if not query_next:
                raise HTTPException(status_code=400, detail="The request body is invalid. (1b)")

        if item.previous == None and item.next == None:
            if query_item[1] == None and query_item[2] == None:
                return {
                    "status": "Nothing to do."
                }
            else:
                raise HTTPException(status_code=400, detail="The request body is invalid. (2)")

        if (item.previous == None) and (item.next != None and query_next[1] == query_item[0]) \
        or (item.previous != None and query_previous[2] == query_item[0]) and (item.next == None) \
        or (item.previous != None and query_previous[2] == query_item[0]) and (item.next != None and query_next[1] == query_item[0]):
            return {
                "status": "Nothing to do."
            }

        if item.previous != None and item.next == None:
            if query_previous[2] != None or query_collection[2] != query_previous[0]:
                raise HTTPException(status_code=400, detail="The request body is invalid. (3)")

            cursor.execute("""
                UPDATE Collections
                SET last = %s
                WHERE id = %s
            """, (query_item[0], collection_id))

            cursor.execute("""
                UPDATE Collection_Items
                SET next = %s
                WHERE id = %s
            """, (query_item[0], query_previous[0]))

            cursor.execute("""
                UPDATE Collection_Items
                SET previous = %s, next = NULL
                WHERE id = %s
            """, (query_previous[0], query_item[0]))

        if item.previous == None and item.next != None:
            if query_next[1] != None or query_collection[1] != query_next[0]:
                raise HTTPException(status_code=400, detail="The request body is invalid. (4)")

            cursor.execute("""
                UPDATE Collections
                SET first = %s
                WHERE id = %s
            """, (query_item[0], collection_id))

            cursor.execute("""
                UPDATE Collection_Items
                SET previous = %s
                WHERE id = %s
            """, (query_item[0], query_next[0]))

            cursor.execute("""
                UPDATE Collection_Items
                SET previous = NULL, next = %s
                WHERE id = %s
            """, (query_next[0], query_item[0]))

        if item.previous != None and item.next != None:
            if query_previous[2] != query_next[0] or query_next[1] != query_previous[0]:
                raise HTTPException(status_code=400, detail="The request body is invalid. (5)")

            cursor.execute("""
                UPDATE Collection_Items
                SET next = %s
                WHERE id = %s
            """, (query_item[0], query_previous[0]))

            cursor.execute("""
                UPDATE Collection_Items
                SET previous = %s
                WHERE id = %s
            """, (query_item[0], query_next[0]))

            cursor.execute("""
                UPDATE Collection_Items
                SET previous = %s, next = %s
                WHERE id = %s
            """, (query_previous[0], query_next[0], query_item[0]))

        if query_item[1]:
            cursor.execute("""
                UPDATE Collection_Items
                SET next = %s
                WHERE id = %s
            """, (query_item[2], query_item[1]))
        else:
            cursor.execute("""
                UPDATE Collections
                SET first = %s
                WHERE id = %s
            """, (query_previous[0], collection_id))

        if query_item[2]:
            cursor.execute("""
                UPDATE Collection_Items
                SET previous = %s
                WHERE id = %s
            """, (query_item[1], query_item[2]))
        else:
            cursor.execute("""
                UPDATE Collections
                SET last = %s
                WHERE id = %s
            """, (query_next[0], collection_id))

        connection.commit()

    return await get_collection(collection_id, api_key)



@router.delete("/collections/{collection_id}/{beer_id}", tags=["collections"])
async def remove_collection_item(collection_id: int, beer_id: int, api_key : APIKey = Depends(get_api_key)):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id, owner
            FROM Collections
            WHERE id = %s
        """, (collection_id,))
        query_collection = cursor.fetchone()

        if not query_collection:
            raise HTTPException(status_code=404, detail="The collection you want to edit does not exist.")

        if api_key["user"] != query_collection[1]:
            raise HTTPException(status_code=403, detail="The collection you want to edit does not belong to you.")

        cursor.execute("""
            SELECT id, previous, next
            FROM Collection_Items
            WHERE beer = %s AND collection = %s
        """, (beer_id, collection_id))
        query_item = cursor.fetchone()

        if not query_item:
            raise HTTPException(status_code=404, detail="The item you want to remove does not exist.")

        if query_item[1]:
            cursor.execute("""
                UPDATE Collection_Items
                SET next = %s
                WHERE id = %s
            """, (query_item[2], query_item[1]))
        else:
            cursor.execute("""
                UPDATE Collections
                SET first = %s
                WHERE id = %s
            """, (query_item[2], collection_id))

        if query_item[2]:
            cursor.execute("""
                UPDATE Collection_Items
                SET previous = %s
                WHERE id = %s
            """, (query_item[1], query_item[2]))
        else:
            cursor.execute("""
                UPDATE Collections
                SET last = %s
                WHERE id = %s
            """, (query_item[1], collection_id))

        cursor.execute("""
            DELETE FROM Collection_Items
            WHERE id = %s
        """, (query_item[0],))

        connection.commit()

    return await get_collection(collection_id, api_key)