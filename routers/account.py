from argon2 import PasswordHasher
from config import connection, get_random_string, search
import datetime
from email_utils import send_email
from fastapi import APIRouter, HTTPException
import jwt
import os
from pydantic import BaseModel
import re
import secrets
import string
import time

router = APIRouter()

alphanumeric_pattern = re.compile("^[a-zA-Z0-9_]+$")
email_pattern = re.compile("^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+$")
password_pattern = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])(?=.{8,})")



class Login(BaseModel):
    username: str
    password: str

@router.post("/users/login", tags=["users"])
async def login(login: Login):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT uuid, username, password_hash
            FROM Users
            WHERE username=%s
        """, (login.username,))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        try:
            PasswordHasher().verify(query_users[2], login.password)
        except:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        now = int(time.time())
        token = jwt.encode(
            {
                "client_id": query_users[0],
                "nickname": query_users[1],
                "iat": now,
                "exp": now + 60 * 60 * 24 * 7 * 6,
            }, os.environ["zythogora_jwt_secret"], algorithm="HS512")

        return { "token": token }



@router.post("/account/login", tags=["account"])
async def loginWithRefresh(login: Login):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT uuid, username, password_hash
            FROM Users
            WHERE username=%s
        """, (login.username,))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        try:
            PasswordHasher().verify(query_users[2], login.password)
        except:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        now = int(time.time())

        # create a new access token that expires in one hour
        access_token_exp = now + 60 * 60
        access_token = jwt.encode(
            {
                "client_id": query_users[0],
                "nickname": query_users[1],
                "iat": now,
                "exp": access_token_exp,
            }, os.environ["zythogora_jwt_secret"], algorithm="HS512")

        # create a new refresh token that expires in two weeks
        alphabet = string.ascii_letters + string.digits
        refresh_token = ''.join(secrets.choice(alphabet) for i in range(512))
        refresh_token_exp = now + 60 * 60 * 24 * 14
        cursor.execute("""
            INSERT INTO Refresh_Tokens
            (user, token, expiration_time)
            VALUES (%s, %s, %s)
        """, (
            query_users[0],
            refresh_token,
            datetime.datetime.fromtimestamp(refresh_token_exp).strftime('%Y-%m-%d %H:%M:%S')
        ))
        connection.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }



class Register(BaseModel):
    firstname: str
    lastname: str
    email: str
    username: str
    password: str
    nationality: int

@router.post("/users/register", tags=["users"])
async def register(register: Register):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT id
            FROM Users
            WHERE username=%s
        """, (register.username, ))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Username already in use")

        if alphanumeric_pattern.match(register.username) is None:
            raise HTTPException(status_code=422, detail="Username contains forbidden characters")

        cursor.execute("""
            SELECT id
            FROM Users
            WHERE email=%s
        """, (register.email, ))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Email already in use")

        if email_pattern.match(register.email) is None:
            raise HTTPException(status_code=422, detail="Email format unknown")

        if password_pattern.match(register.password) is None:
            raise HTTPException(status_code=422, detail="Password must meet requirements (at least 8 characters, one uppercase and one lowercase letter, one number and one special case character)")

        cursor.execute("""
            SELECT id
            FROM Countries
            WHERE id=%s
        """, (register.nationality, ))
        if not cursor.fetchone():
            raise HTTPException(status_code=422, detail="Country unknown")

        cursor.execute("""
            INSERT INTO Users
            (firstname, lastname, username, email, password_hash, nationality)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            register.firstname,
            register.lastname,
            register.username,
            register.email,
            PasswordHasher().hash(register.password),
            register.nationality
        ))
        connection.commit()

        cursor.execute("""
            SELECT uuid
            FROM Users
            WHERE id=%s
        """, (cursor.lastrowid, ))
        query_users = cursor.fetchone()

        now = int(time.time())
        token = jwt.encode(
            {
                "client_id": query_users[0],
                "nickname": register.username,
                "iat": now,
                "exp": now + 60 * 60 * 3,
            }, os.environ["zythogora_jwt_secret"], algorithm="HS512")

        return { "token": token }



class RecoverAccount(BaseModel):
    email: str

@router.post("/account/recover", tags=["account"])
async def recover_account(recover_account: RecoverAccount):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        if email_pattern.match(recover_account.email) is None:
            raise HTTPException(status_code=422, detail="Email format unknown")

        cursor.execute("""
            SELECT uuid, username
            FROM Users
            WHERE email=%s
        """, (recover_account.email,))
        query_users = cursor.fetchone()

        if query_users:
            recover_key = get_random_string(64)

            cursor.execute("""
                INSERT INTO Password_Reset_Keys
                (user, password_reset_key)
                VALUES (%s, %s)
            """, (
                query_users[0],
                recover_key
            ))
            connection.commit()

            content = """
                <p>
                    Somebody, probably you, requested to reset the password of the Zythogora account associated with this email. <br />
                    If you indeed requested this password reset, please click on the following button. <br />
                    Be aware that the link is available only for 10 minutes. Past that delay, you will need to request a new link to recover your account! <br />
                    If you do not want to reset your password or did not perform any request to do so, please ignore this email. Your password will not be changed until you click the button below and create a new one.
                </p>
                <a
                    href=\"https://zythogora.com/account/reset_password?email={email}&key={key}\"
                    style=\"
                        display: inline-block;
                        margin: 0 20px 5px 20px;
                        padding: 20px;
                        border-radius: 5px;
                        background-color: #ffb340;
                        color: #fff;
                        font-weight: bold;
                        text-decoration: none;
                    \"
                    >Reset your password</a
                >
                <p style=\"font-size: 12px\">
                    Alternatively, you can copy this link to your favorite browser:
                    <a
                        href=\"https://zythogora.com/account/reset_password?email={email}&key={key}\"
                        class=\"link\"
                        style=\"
                            color: #bc7100;
                            font-weight: bold;
                            text-decoration: none;
                        \"
                        >https://zythogora.com/account/reset_password?email={email}&key={key}</a
                    >
                </p>
            """.format(email=recover_account.email, key=recover_key)

            send_email(recover_account.email, "Zythogora - Account Recovery", content, query_users[0])

        return { "message": f"If an account is associated with the email {recover_account.email}, you will receive an email with a link to reset your password." }



class ResetPassword(BaseModel):
    password_reset_key: str
    email: str
    password: str

@router.post("/account/resetPassword", tags=["account"])
async def reset_password(reset_password: ResetPassword):
    connection.ping(reconnect=True)
    with connection.cursor(prepared=True) as cursor:
        if alphanumeric_pattern.match(reset_password.password_reset_key) is None or len(reset_password.password_reset_key) != 64:
            raise HTTPException(status_code=422, detail="Invalid key")

        if email_pattern.match(reset_password.email) is None:
            raise HTTPException(status_code=422, detail="Email format unknown")

        if password_pattern.match(reset_password.password) is None:
            raise HTTPException(status_code=422, detail="Password must meet requirements (at least 8 characters, one uppercase and one lowercase letter, one number and one special case character)")

        cursor.execute("""
            SELECT uuid, username
            FROM Users
            WHERE email=%s
        """, (reset_password.email,))
        query_users = cursor.fetchone()

        if not query_users:
            raise HTTPException(status_code=401, detail="The key does not exist, has expired or is not associated with your account")

        cursor.execute("""
            SELECT id, request_time
            FROM Password_Reset_Keys
            WHERE user=%s AND password_reset_key=%s
        """, (query_users[0], reset_password.password_reset_key))
        query_keys = cursor.fetchone()

        if not query_keys:
            raise HTTPException(status_code=401, detail="The key does not exist, has expired or is not associated with your account")

        if datetime.datetime.now() > query_keys[1] + datetime.timedelta(minutes=10):
            cursor.execute("""
                DELETE FROM Password_Reset_Keys
                WHERE id=%s
            """, (query_keys[0],))
            connection.commit()
            raise HTTPException(status_code=401, detail="The key does not exist, has expired or is not associated with your account")

        cursor.execute("""
            UPDATE Users
            SET password_hash=%s
            WHERE uuid=%s
        """, (
            PasswordHasher().hash(reset_password.password),
            query_users[0]
        ))
        connection.commit()

        #TODO: Disconnect all logged in users

        content = """
            <p>
                You've just updated your Zythogora password! <br />
                If you did <b>NOT</b> perform this change, please <a href=\"https://zythogora.com/account/recover\">reset your password</a> immediately. <br />
                If this was you, then no further action is required.
            </p>
        """

        send_email(reset_password.email, "Zythogora - Password Change", content, query_users[0])

        cursor.execute("""
            DELETE FROM Password_Reset_Keys
            WHERE id=%s
        """, (query_keys[0],))
        connection.commit()

        return { "message": f"The password has been reset successfully." }
