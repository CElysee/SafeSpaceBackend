from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from fastapi.staticfiles import StaticFiles

from routes import (auth, country,YogaSessions, MembershipBookings, YogaClassLocation, YogaClassBooking, Planning)
from routes.auth import get_current_user, user_dependency

import models
from database import engine, db_dependency
import os
from cachetools import TTLCache

app = FastAPI()
# Configure CORS middleware
# origins = ["*"]  # Replace "*" with your frontend's domain(s) for production
app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["http://localhost:5173", "https://app.safespaceyoga.rw"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get('/', status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    user = db.query(models.User).all()
    return user


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
