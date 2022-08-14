from config import connection, get_random_string
from email.utils import formataddr
from email.message import EmailMessage
import os
import smtplib, ssl


port = 587
smtp_server = os.environ["zythogora_email_server"]

email_username = os.environ["zythogora_email_username"]
email_password = os.environ["zythogora_email_password"]

context = ssl.create_default_context()


def get_message(sender, sender_name, receiver, subject, content, receiver_uuid, is_unsubscribable):
    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            SELECT username
            FROM Users
            WHERE uuid=%s
        """, (receiver_uuid,))
        query_users = cursor.fetchone()

        if not query_users:
            return None

        if is_unsubscribable:
            unsubscription_key = get_random_string(64)

            cursor.execute("""
                INSERT INTO Email_Unsubscription_Keys
                (user, unsubscription_key, email_subject)
                VALUES (%s, %s, %s)
            """, (
                receiver_uuid,
                unsubscription_key,
                subject
            ))
            connection.commit()

    msg = EmailMessage()
    msg["From"] = formataddr((sender_name, sender))
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.set_content("""
        <!DOCTYPE html>
        <html>
            <head>
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            </head>
            <body
                style=\"
                    width: min(700px, 100%);
                    margin: auto;
                    font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;
                    color: #000;
                    overflow-wrap: break-word;
                \"
            >
                <div
                    style=\"background-color: #ffb340; padding: 30px; text-align: center\"
                >
                    <h1 style=\"margin: 0; font-size: 32px; text-transform: uppercase\">
                        Zythogora
                    </h1>
                    <h3 style=\"margin: 0; font-size: 14px; text-transform: uppercase\">
                        The Beer Gathering Place
                    </h3>
                </div>
                <div class=\"content\" style=\"padding: 30px\">
                    <p>
                        Hi {username},
                    </p>
    """.format(username=query_users[0]) + content + """
                    <p style=\"margin-top: 30px\">
                        Cheers, <br />
                        The Zythogora Team
                    </p>
                </div>
                <div
                    style=\"
                        background-color: #ddd;
                        padding: 30px;
                        text-align: center;
                        font-size: 12px;
                    \"
                >
                    <p>
                        If you have any question about the app or if you want to give us
                        your feedback,<br />
                        you can send us an email at
                        <a
                            href=\"mailto:contact@zythogora.com\"
                            class=\"link\"
                            style=\"
                                color: #bc7100;
                                font-weight: bold;
                                text-decoration: none;
                            \"
                            >contact@zythogora.com</a
                        >.
                    </p>
    """ + ("" if not is_unsubscribable else """
                    <a
                        href=\"https://zythogora.com/account/emails/unsubscribe/{key}\"
                        class=\"link\"
                        style=\"color: #999; text-decoration: none\"
                        >Unsubscribe</a
                    >
    """.format(key=unsubscription_key)) + """
                </div>
            </body>

            <style>
                .link:hover {
                    text-decoration: underline !important;
                }
                @media (min-width: 700px) {
                    .content {
                        padding: 75px 100px !important;
                    }
                }
            </style>
        </html>
    """, subtype="html")
    return msg

def send_email(receiver, subject, content, receiver_uuid, is_unsubscribable=False):
    message = get_message(
        email_username, "Zythogora",
        receiver,
        subject,
        content,
        receiver_uuid,
        is_unsubscribable
    )

    if not message:
        return False

    with connection.cursor(prepared=True) as cursor:
        cursor.execute("""
            INSERT INTO Emails_Sent
            (user, email_subject)
            VALUES (%s, %s)
        """, (
            receiver_uuid,
            subject
        ))
        connection.commit()

    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(email_username, email_password)
        server.send_message(message)

    return True