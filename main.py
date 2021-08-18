from fastapi import FastAPI

from routers import beers, breweries, countries, ratings, styles, users


app = FastAPI()
app.include_router(beers.router)
app.include_router(breweries.router)
app.include_router(countries.router)
app.include_router(ratings.router)
app.include_router(styles.router)
app.include_router(users.router)




from config import connection
import atexit

@atexit.register
def close_connection():
    connection.close()
