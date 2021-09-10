from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from models import *

app = FastAPI(title="E-commerce API")


@app.get("/")
async def index():
    return {"message": "hello world"}


register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
