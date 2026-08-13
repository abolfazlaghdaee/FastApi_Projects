from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from starlette import status
from pydantic import BaseModel
from MediaLoop.router import auth, posts
from MediaLoop.models import Posts 
from MediaLoop.db import  sessionlocal, engine
from sqlalchemy.orm import Session
from typing import Annotated
from sqlalchemy import select
import MediaLoop.models as models
from MediaLoop.images import imagekit
from imagekitio.types import FileUploadResponse
import os
import shutil
import uuid
import tempfile
from MediaLoop.router import users

app = FastAPI()




models.Base.metadata.create_all(bind= engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)

@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

