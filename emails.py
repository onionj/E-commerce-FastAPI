from typing import List

from models import User

from fastapi import (FastAPI, status, BackgroundTasks,
                     UploadFile, File, Form, Depends, HTTPException, )
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel
from pydantic import BaseModel, EmailStr
import jwt

from config import get_settings

SITE_URL = "http://localhost:8000/"
SITE_NAME = "Nice shop"


conf = ConnectionConfig(
    MAIL_USERNAME=get_settings().MAIL_USERNAME,
    MAIL_PASSWORD=get_settings().MAIL_PASSWORD,
    MAIL_FROM=get_settings().MAIL_FROM,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_mail(email: List[EmailStr], instance: User):
    """send Account Verification mail"""

    token_data = {
        "id": instance.id,
        "username": instance.username
    }

    token = jwt.encode(token_data, get_settings().SECRET, algorithm="HS256")

    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div style = "display:flex; align-items: center; flex-direction: column" >
            <h3>Account Verification</H3>

            <br>

            <p>
                Thanx for choosing us, please click on the button below
                to verify your account
            </p> 
            
            <a style = "display:marign-top: 1rem ; padding: 1rem; border-redius: 0.5rem;
             font-size:1rem; text-decoration: no; background: #0275d8; color:white"
             href="{SITE_URL}verification/?token={token}>
                Verify your email
             </a>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject=SITE_NAME,
        recipients=email,  # List of recipients,
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
