from re import U
from fastapi import Depends, APIRouter, HTTPException, status, Cookie
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from db.client import db_client
from db.schemas.user import user_schema
from models.user import User

SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str or None = None


class UserWithId(User):
    id: str


class UserInDB(User):
    password: str


router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = "ee379b236cbdbfd54f0f963bd4753fd8eb1e04b2c2066575cd84272fc8dcd8bc"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return bcrypt_context.hash(password)


def get_user(username: str):
    user = db_client.users.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"]) if "_id" in user else None
        hashed_password = user.get("password", "")
        user_in_db = UserInDB(id=user["_id"], username=user["username"], first_name=user["first_name"],
                              last_name=user["last_name"], email=user["email"], password=hashed_password)
        return user_in_db
    return None


def verifyPassword(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return None
    if not verifyPassword(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_bearer)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credential_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(request_data: dict):
    username = request_data.get("username")
    password = request_data.get("password")
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required",
        )

    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": f"{user.first_name} {user.last_name}"
    }

    response_content = {
        "user": user_info,
        "access_token": access_token
    }
    response = JSONResponse(content=response_content)
    return response


@router.get("/users/me/", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return current_user
