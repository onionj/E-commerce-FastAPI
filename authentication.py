from passlib.context import CryptContext
from passlib.utils.decor import deprecated_function
from fastapi import HTTPException, status
import jwt

from models import User
from config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password):
    return pwd_context.hash(password)


async def very_token(token: str):
    try:

        payload = jwt.decode(token, get_settings().SECRET,
                             algorithms=["HS256"])
        user = await User.get(id=payload.get("id"))
        return user

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
