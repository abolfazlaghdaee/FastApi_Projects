from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

import models as models
from db import engine
from router import auth, posts, users

app = FastAPI(title="MediaLoop")

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)

# Web frontend (plain HTML/CSS/JS) served from the same origin as the API.
FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/")
