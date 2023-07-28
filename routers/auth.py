from sys import path

path.append("..")

from models import User
from database import user_collection
from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import DuplicateKeyError
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import Optional
from datetime import datetime, timedelta
from config import SECRET_KEY

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
router = APIRouter(prefix="/auth", tags=["Authentication"])

ALGORITHM = "HS256"


async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload = jwt.decode(payload.get("token"), SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")

        if not username or not user_id:
            raise get_user_exception()

        return {"username": username, "id": user_id}
    except JWTError as e:
        raise get_user_exception(e)


def authenticate_user(username: str, password: str):
    attempted_user = user_collection.find_one({"username": username})
    if attempted_user:
        user = User(
            username=attempted_user.get("username"),
            email=attempted_user.get("email"),
            hashed_password=attempted_user.get("hashed_password"),
        )

        if user.check_password_correction(password):
            return attempted_user

    return False


def create_access_token(
    username: str, user_id: str, expires_delta: Optional[timedelta] = None
):
    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(user_model: User):
    try:
        username = user_model.username
        email = user_model.email
        user = User(username=username, email=email)
        user.password = user_model.hashed_password
        user_collection.insert_one(user.model_dump())

    except DuplicateKeyError as e:
        duplicate_key = e.details.get("keyPattern", {})
        conflicting_field = next(iter(duplicate_key.keys()), None)

        if conflicting_field == "username":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An user with the same username already exists",
            )
        elif conflicting_field == "email":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An user with the same email already exists",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An user with conflicting data already exists",
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong!",
        )


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise token_exception()

    token = create_access_token(
        username=user.get("username"),
        user_id=str(user.get("_id")),
    )

    return {"token": token}


# Exceptions
def get_user_exception(e: Exception):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate credentials. Error msg: {e}",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception


def token_exception():
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return token_exception_response
