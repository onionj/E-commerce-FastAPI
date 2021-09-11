from passlib.context import CryptContext
from passlib.utils.decor import deprecated_function

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password):
    return pwd_context.hash(password)
