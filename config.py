from pydantic import BaseSettings

class Settings(BaseSettings):
    zythogora_db_username: str
    zythogora_db_password: str

    class Config:
        env_file = "db_credentials"

settings = Settings()



import mysql.connector as database

connection = database.connect(
    user=settings.zythogora_db_username,
    password=settings.zythogora_db_password,
    host="localhost",
    database="Zythogora"
)

cursor = connection.cursor(prepared=True)
