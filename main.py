
from fastapi import (FastAPI, status, Request,
                     HTTPException, Depends, Query)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# database
from tortoise.contrib.fastapi import register_tortoise
from models import (User, Business, Product,
                    user_pydantic, user_pydanticIn, user_pydanticOut, users_pydanticOut,
                    business_pydantic, business_pydanticIn,
                    product_pydantic, product_pydanticIn)

# authentication
from authentication import (get_hashed_password,
                            very_token, very_token_email,
                            is_not_email, token_generator)
from fastapi.security import (OAuth2PasswordBearer, OAuth2PasswordRequestForm)

# signal
from tortoise.signals import post_save
from tortoise import BaseDBAsyncClient
from typing import List, Optional, Type

# email
from emails import send_mail

# images
from fastapi import File, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import Image
import secrets

# env file
from config import get_settings
SITE_URL = get_settings().SITE_URL


app = FastAPI(title="E-commerce API", version="0.1.1",
              description=" E-commerce API created with FastAPI and jwt Authenticated")


oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

# static file setup config
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/token", tags=["User"])
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth_scheme)):
    return await very_token(token)


@app.post("/users/me", tags=["User"])
async def client_data(user: user_pydanticIn = Depends(get_current_user)):

    business = await Business.get(owner=user)
    logo = business.logo
    logo = f'{SITE_URL}{logo}'

    return {
        "status": "ok",
        "data": {
            "username": user.username,
            "email": user.email,
            "is_verifide": user.is_verifide,
            "join_date": user.join_date.strftime("%b %d %Y"),
            "logo": logo,
            "business": await business_pydantic.from_tortoise_orm(business)
        }
    }


@app.get("/users/", tags=["User"], response_model=List[users_pydanticOut])
async def get_users(user: user_pydanticIn = Depends(get_current_user),
                    limit: int = Query(100, le=100),
                    skip: int = Query(0, ge=0)
                    ):

    users = await User.filter(id__gt=skip, id__lte=skip+limit)
    return users


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


@app.post("/users/", tags=["User"], status_code=status.HTTP_201_CREATED, response_model=user_pydanticOut)
async def user_registration(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)

    # This is a bad way to do it:
    # TODO fix this, create custom 'user_pydanticIn for validate data '
    if len(user_info["password"]) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be longer than 8 characters")
    if len(user_info["username"]) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be longer than 5 characters")
    if is_not_email(user_info["email"]):
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


@app.get("/verification/email", response_class=HTMLResponse, tags=["User"])
async def email_verification(request: Request, token: str):
    user = await very_token_email(token)
    if user:
        if not user.is_verifide:
            user.is_verifide = True
            await user.save()
        context = {
            "request": request,
            "is_verifide": user.is_verifide,
            "username": user.username
        }
        return template.TemplateResponse("verification.html", context)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Token or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.post("/uploadfile/profile", tags=["User"])
async def upload_profile_image(file: UploadFile = File(..., max_lenght=10485760),
                               user: user_pydantic = Depends(get_current_user)):

    FILEPATH = "./static/images/"
    file_name = file.filename

    try:
        extension = file_name.split(".")[1]
    finally:
        if extension not in ["png", "jpg", "jpeg"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="File extension not allowed")

    token_name = "logo" + secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, "wb") as f:
        f.write(file_content)

    # PILLOW
    img = Image.open(generated_name)
    img = img.resize(size=(200, 200))
    img.save(generated_name)

    business = await Business.get(owner=user)
    owner = await business.owner

    if owner == user:
        business.logo = generated_name[1:]
        await business.save()
        return await business_pydantic.from_tortoise_orm(business)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to perform this action",
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.post("/uploadfile/product/{id}", tags=["Product"])
async def upload_product_image(
        id: int,
        file: UploadFile = File(..., max_lenght=10485760),
        user: user_pydantic = Depends(get_current_user)):

    FILEPATH = "./static/images/"
    file_name = file.filename

    try:
        extension = file_name.split(".")[1]
    finally:
        if extension not in ["png", "jpg", "jpeg"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="File extension not allowed")

    token_name = "product" + secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, "wb") as f:
        f.write(file_content)

    product = await Product.get_or_none(id=id)
    if product:
        business = await product.business
        owner = await business.owner
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Not Found"
        )
    if owner == user:
        product.product_image = generated_name[1:]
        await business.save()
        return await product_pydantic.from_tortoise_orm(product)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to perform this action",
            headers={"WWW-Authenticate": "Bearer"}
        )

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
)
