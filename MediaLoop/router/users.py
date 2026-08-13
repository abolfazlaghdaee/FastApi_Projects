from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, HTTPException, Path
import models
from models import Users, RevokedToken
from models import RevokedToken
from db import  sessionlocal
from starlette import status
from .auth import get_current_user
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer



router = APIRouter(
    prefix = '/users',
    tags = ['users']
)



def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()



db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')
bycrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')



class userverification(BaseModel):
    password :str
    new_password : str = Field(min_length = 6)



@router.get('/',status_code= status.HTTP_200_OK)
async def get_user(db: db_dependency, user_id : user_dependency):
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
      
    user_info = db.query(Users).filter(user_id.get('id') == Users.id).first()

    return user_info



@router.put('/password',status_code= status.HTTP_202_ACCEPTED)
async def change_password(db: db_dependency, user_id : user_dependency, user_verfication : userverification):
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

    user_info = db.query(Users).filter(user_id.get('id') == Users.id).first() 

    if not bycrypt_context.verify(user_verfication.password , user_info.hash_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Error on password change')


    user_info.hash_password = bycrypt_context.hash(user_verfication.new_password)
    db.add(user_info)
    db.commit()

    


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: Annotated[str, Depends(oauth2_scheme)],user_id: user_dependency,
    db: db_dependency):
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user")

    revoked_token = RevokedToken(token=token)

    db.add(revoked_token)
    db.commit()

    return {
        "message": "Successfully logged out"
    }





@router.delete('/',status_code=status.HTTP_200_OK)
async def delete_user( db: db_dependency, current_user: user_dependency):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

    user = db.query(Users).filter(Users.id == current_user.get('id')).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


    
