from fastapi import FastAPI, status, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# database
from authentication import (get_hashed_password, very_token, not_email)
from tortoise.contrib.fastapi import register_tortoise
from models import (User, Business, Product,
                    user_pydantic, user_pydanticIn, user_pydanticOut,
                    business_pydantic, business_pydanticIn,
                    product_pydantic, product_pydanticIn)

# signal
from tortoise.signals import post_save
from tortoise import BaseDBAsyncClient
from typing import List, Optional, Type

# email
from emails import send_mail


app = FastAPI(title="E-commerce API", version="0.0.3")


@post_save(User)
async def create_business(
        sender: "Type[User]",
        instance: User,
        created: bool,
        using_db: "Optional[BaseDBAsyncClient]",
        update_fields: List[str]) -> None:
    if created:
        business_obj = await Business.create(
            business_name=instance.username,
            owner=instance)
        await business_pydantic.from_tortoise_orm(business_obj)
        # send the email
        await send_mail([instance.email], instance)


@app.post("/registration/", tags=["User"], status_code=status.HTTP_201_CREATED, response_model=user_pydanticOut)
async def user_registration(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)

    # This is a bad way to do it:
    # TODO fix this
    if len(user_info["password"]) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be longer than 8 characters")
    if len(user_info["username"]) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be longer than 5 characters")
    if not_email(user_info["email"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This is not a valid email")

    if await User.exists(username=user_info.get("username")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    if await User.exists(email=user_info.get("email")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user_info["password"] = get_hashed_password(user_info["password"])

    user_obj = await User.create(**user_info)
    user_new = await user_pydanticOut.from_tortoise_orm(user_obj)
    return user_new


template = Jinja2Templates(directory="templates")


@app.get("/verification", response_class=HTMLResponse, tags=["User"])
async def email_verification(request: Request, token: str):
    user = await very_token(token)
    if user:
        if not user.is_verifide:
            user.is_verifide = True
            await user.save()
        return template.TemplateResponse("verification.html", {"request": request, "username": user.username})

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Token or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )


register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
