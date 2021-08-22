from fastapi import FastAPI

from routers import beers, breweries, colors, countries, ratings, servings, styles, users


app = FastAPI()
app.include_router(beers.router)
app.include_router(breweries.router)
app.include_router(colors.router)
app.include_router(countries.router)
app.include_router(ratings.router)
app.include_router(servings.router)
app.include_router(styles.router)
app.include_router(users.router)




from config import connection
import atexit

@atexit.register
def close_connection():
    connection.close()
