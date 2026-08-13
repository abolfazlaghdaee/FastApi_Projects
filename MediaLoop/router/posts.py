from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from starlette import status
from pydantic import BaseModel
from models import Posts , Users
from db import  sessionlocal, engine
from sqlalchemy.orm import Session
from typing import Annotated
from sqlalchemy import select,and_
# import models
from images import imagekit
from imagekitio.types import FileUploadResponse
import os
import shutil
import uuid
import tempfile
from .auth import get_current_user


router = APIRouter(
    prefix = "/posts",
    tags = ["Posts"]
)





def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]



class text_posts_request(BaseModel):
    title:str 
    content :str





@router.post('/')
async def upload_file(db: db_dependency, user_id: user_dependency ,file: UploadFile = File(...),caption: str = Form("")):
    try:

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

        


        # 1. Read file directly from FastAPI stream to save memory (no temp files needed)
        file_bytes = await file.read()

        # 2. Call the correct modern v4 method (files.upload) with flat arguments
        upload_result = imagekit.files.upload(
            file=file_bytes,
            file_name=file.filename,
            use_unique_file_name=True,
            tags=["backend", "fastapi"]
        )

        # 3. Dynamic type mapping based on the incoming file stream
        is_video = file.content_type and file.content_type.startswith("video/")
        detected_file_type = "video" if is_video else "image"

        # 4. Create and save the Post record using actual details from the upload response
        post = Posts(
            caption=caption, 
            url=upload_result.url, 
            file_type=detected_file_type, 
            file_name=upload_result.name,
            owner_id=user_id.get('id')  # Use the actual user ID from the dependency
        )
        
        db.add(post)
        db.commit() 
        db.refresh(post)
        
        return post

    except Exception as e:
        # Roll back your database transaction so it doesn't leave uncommitted sessions open
        db.rollback()
        # Never use 'pass' here, always inform the API client what went wrong
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail='An error occurred while uploading the file: ' + str(e))

    finally:
        # Safely shut down the local inbound file stream
        await file.close()






@router.get('/feed')
async def get_feed(db: db_dependency):
    result = db.execute(select(Posts).order_by(Posts.created_at.desc()))

    posts= [row[0] for row in result]

    resutls = db.execute(select(Users))
    users = [row[0] for row in resutls.all()]

    user_dict = {user.id: user.email for user in users}

    posts_data = []

    for post in posts:
        post_data = {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
            "is owner": post.owner_id == user_dict.get(post.owner_id),  # Check if the post owner matches the user
            "email":  user_dict.get(post.owner_id, "Unknown")  # Default to "Unknown" if user not found
        }
        posts_data.append(post_data)


    return {"posts": posts_data}
    

@router.delete('/delete/{post_id}')
async def delete_post(post_id: str, db: db_dependency, user_id: user_dependency):
    try:

       if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

       

       result = db.execute(select(Posts).where(and_(Posts.id == post_id,Posts.owner_id == int(user_id.get("id"))))) 
       post = result.scalars().first()

       if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

       db.delete(post)
       db.commit()
       return {"message": "Post deleted successfully"}


    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")
