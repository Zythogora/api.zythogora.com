from fastapi import FastAPI

from routers import account, beers, breweries, collections, colors, countries, ratings, servings, styles, top, users

description = """
The API behind [Zythogora](https://zythogora.com).
![](https://thumbs.gfycat.com/FelineHandsomeCowrie-size_restricted.gif)
"""

app = FastAPI(
    title = "Zythogora API",
    description = description,
    version = "0.0.1",
)


app.include_router(account.router)
app.include_router(beers.router)
app.include_router(breweries.router)
app.include_router(collections.router)
app.include_router(colors.router)
app.include_router(countries.router)
app.include_router(ratings.router)
app.include_router(servings.router)
app.include_router(styles.router)
app.include_router(top.router)
app.include_router(users.router)




from config import connection
import atexit

@atexit.register
def close_connection():
    connection.close()
