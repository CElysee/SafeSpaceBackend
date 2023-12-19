from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import db_dependency
from starlette import status
from models import YogaClassLocation
from schemas import YogaClassLocationCreate, YogaClassLocationUpdate
from typing import List, Optional, Annotated

router = APIRouter(
    tags=["YogaClassLocation"],
    prefix='/yoga_class_location'
)


@router.get("/list")
async def get_yoga_class_location(db: db_dependency):
    yoga_class_location_list = db.query(YogaClassLocation).all()
    return yoga_class_location_list


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_yoga_class_location(yoga_class_location: YogaClassLocationCreate, db: db_dependency):
    check_yoga_class_location = db.query(YogaClassLocation).filter(
        YogaClassLocation.name == yoga_class_location.name).first()
    if check_yoga_class_location:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaClassLocation already exists")

    yoga_class_location = YogaClassLocation(
        name=yoga_class_location.name,
        address=yoga_class_location.address,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(yoga_class_location)
    db.commit()
    db.refresh(yoga_class_location)
    return {"message": "Yoga Class  Location created successfully", "data": yoga_class_location}


@router.get("/{id}")
async def get_yoga_class_location(id: int, db: db_dependency):
    yoga_class_location = db.query(YogaClassLocation).filter(YogaClassLocation.id == id).first()
    if yoga_class_location is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaClassLocation does not exist")
    return yoga_class_location


@router.put("/update/{id}")
async def update_yoga_class_location(id: int, yoga_class_location: YogaClassLocationUpdate, db: db_dependency):
    check_yoga_class_location = db.query(YogaClassLocation).filter(YogaClassLocation.id == id).first()
    if check_yoga_class_location is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaClassLocation does not exist")
    # Define the update values in a dictionary
    update_values = {
        "name": yoga_class_location.name,
        "address": yoga_class_location.address,
    }
    db.query(YogaClassLocation).filter(YogaClassLocation.id == id).update(update_values)
    db.commit()
    return {"message": "Yoga Class Location updated successfully"}


@router.delete("/delete/{id}")
async def delete_yoga_class_location(id: int, db: db_dependency):
    check_yoga_class_location = db.query(YogaClassLocation).filter(YogaClassLocation.id == id).first()
    if check_yoga_class_location is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaClassLocation does not exist")
    db.query(YogaClassLocation).filter(YogaClassLocation.id == id).delete()
    db.commit()
    return {"message": "Yoga Class Location deleted successfully"}
