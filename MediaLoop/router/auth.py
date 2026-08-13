from datetime import timedelta,datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import Users ,RevokedToken

from typing import Annotated
from db import sessionlocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError


router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


bycrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')

SECRET_KEY = 'c7140641098be313ab8b2408c8b52c8856c6b053e90e479e85a5ec5cf6176c6f'
ALGORITHM ='HS256'

class user_request(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    user_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    hash_password: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
   


class Token(BaseModel):
    access_token :str
    token_type: str



def get_db():

    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


db_dependacy = Annotated[Session, Depends(get_db)]

def user_authentication(user_name: str, password: str, db: db_dependacy):
    user = db.query(Users).filter(Users.user_name == user_name).first()
    if not user:
        return False
    if not bycrypt_context.verify(password, user.hash_password):
        return False

    return user

def create_access_token(user_name: str, user_id: int, role: str, expire_time :timedelta):
    encode = {'sub': user_name, 'id': user_id, 'role': role}
    expires = datetime.utcnow() + expire_time
    encode.update(({'exp': expires}))

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# async def get_current_user(token:Annotated[str, Depends(oauth2_scheme)]):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_name: str = payload.get('sub')
#         user_id: int = payload.get('id')
#         role :str = payload.get('role')

#         if user_name is None or user_id is None:
#                 raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')


#         return {'username': user_name, 'id': user_id, 'role': role}

#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

  
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],db: db_dependacy):
    # First check whether the token was revoked
    revoked = (
        db.query(RevokedToken)
        .filter(RevokedToken.token == token)
        .first()
    )

    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user"
            )

        return {"id": user_id}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )



@router.post('/', status_code=status.HTTP_201_CREATED)
async def add_user(db :db_dependacy,  user_request: user_request):
   
    create_user_model = Users(
        first_name = user_request.first_name,
        last_name = user_request.last_name,
        user_name = user_request.user_name,
        email = user_request.email,
        hash_password = bycrypt_context.hash(user_request.hash_password),
        role = user_request.role
    )



    db.add(create_user_model)
    db.commit()


@router.post('/token')
async def login_token(form_data : Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependacy):
    user  = user_authentication(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    


    token = create_access_token(user.user_name, user.id, user.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}





