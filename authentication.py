import re
from passlib.context import CryptContext
from fastapi import HTTPException, status
import jwt

from models import User
from config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password):
    return pwd_context.hash(password)


async def very_token(token: str):
    '''verify token from login'''
    try:
        payload = jwt.decode(token, get_settings().SECRET,
                             algorithms=["HS256"])
        user = await User.get(id=payload.get("id"))

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return await user


async def very_token_email(token: str):
    '''verify token from email'''
    try:
        payload = jwt.decode(token, get_settings().SECRET,
                             algorithms=["HS256"])
        user = await User.get(id=payload.get("id"), email=payload.get("email"))

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return await user

# bug: sam_ple@gma.com:Trye ; sam_p_le@gma.com: False!!
regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'


def is_not_email(email):
    """if valid mail: return 'True' \n 
     ** This is a simple way to do this and is not recommended for a real project ** """
    if(re.search(regex, email)):
        return False
    else:
        return True


async def verify_password(plain_password, database_hashed_password):
    return pwd_context.verify(plain_password, database_hashed_password)


async def authenticate_user(username: str, password: str):
    user = await User.get(username=username)
    if user and verify_password(password, user.password):
        if not user.is_verifide:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verifide",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    return False


async def token_generator(username: str, password: str):
    user = await authenticate_user(username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = {
        "id": user.id,
        "username": user.username
    }
    token = jwt.encode(token_data, get_settings().SECRET, algorithm="HS256")
    return token
