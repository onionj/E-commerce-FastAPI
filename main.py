from fastapi import FastAPI, status
from tortoise.contrib.fastapi import register_tortoise
from models import *
from authentication import (get_hashed_password)

# signal
from tortoise.signals import post_save
from tortoise import BaseDBAsyncClient
from typing import List, Optional, Type

app = FastAPI(title="E-commerce API", version="0.0.2")


@post_save
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


@app.post("/registration/", tags=["User"], status_code=status.HTTP_201_CREATED)
async def user_registration(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)
    user_info["password"] = get_hashed_password(user_info["password"])
    user_obj = await User.create(**user_info)
    user_new = await user_pydantic.from_tortoise_orm(user_obj)
    return user_new.dict()

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
