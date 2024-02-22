import secrets
from importlib import metadata

from fastapi import FastAPI, HTTPException, Depends
# from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import UJSONResponse
from starlette import status
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from routes import (auth, country, YogaSessions, MembershipBookings, YogaClassLocation, YogaClassBooking, Planning)
from routes.auth import get_current_user, user_dependency

import models
from database import engine, db_dependency
import os
from cachetools import TTLCache
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(
    title="FastAPI",
    version=metadata.version("FastAPI"),
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
    default_response_class=UJSONResponse,
)
# Configure CORS middleware
# origins = ["*"]  # Replace "*" with your frontend's domain(s) for production
app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["http://localhost:5173", "http://app.safespaceyoga.rw" "https://app.safespaceyoga.rw", "https://app.safespaceyoga.rw:8000", "http://app.safespaceyoga.rw:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBasic()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(country.router)
app.include_router(YogaSessions.router)
app.include_router(MembershipBookings.router)
app.include_router(YogaClassLocation.router)
app.include_router(YogaClassBooking.router)
app.include_router(Planning.router)

app.mount("/CarSellImages", StaticFiles(directory="CarSellImages"), name="images")
# Your cache instance, replace with your specific cache implementation
cache = TTLCache(maxsize=100, ttl=600)  # TTLCache as an example, use your actual cache implementation


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "Attack@2017_!")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", response_class=HTMLResponse)
async def get_docs(username: str = Depends(get_current_username)) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="docs")


@app.get("/redoc", response_class=HTMLResponse)
async def get_redoc(username: str = Depends(get_current_username)) -> HTMLResponse:
    return get_redoc_html(openapi_url="/api/openapi.json", title="redoc")


@app.get("/UserProfiles/{filename}")
async def get_image(filename: str):
    """Get an image by filename."""
    if not os.path.exists(f"CarSellImages/{filename}"):
        raise HTTPException(status_code=404, detail="Image not found")

    with open(f"CarSellImages/{filename}", "rb") as f:
        image_data = f.read()

    return image_data


@app.post("/clear_cache")
def clear_cache():
    cache.clear()
    return {"message": "Cache cleared successfully"}
