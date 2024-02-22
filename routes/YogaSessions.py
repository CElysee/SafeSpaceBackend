from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import db_dependency
from starlette import status
from models import YogaSessions
from typing import List, Optional, Annotated

from schemas import YogaSessionsCreate, YogaSessionsUpdate

router = APIRouter(
    tags=["YogaSessions"],
    prefix='/yoga_sessions'
)


@router.get("/list")
async def get_yoga_sessions(db: db_dependency):
    yoga_sessions_list = db.query(YogaSessions).all()
    return yoga_sessions_list


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_yoga_sessions(yoga_sessions: YogaSessionsCreate, db: db_dependency):
    check_yoga_sessions = db.query(YogaSessions).filter(YogaSessions.name == yoga_sessions.name).first()
    if check_yoga_sessions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaSessions already exists")

    yoga_sessions = YogaSessions(
        name=yoga_sessions.name,
        price=yoga_sessions.price,
        number_of_classes=yoga_sessions.number_of_classes,
        description=yoga_sessions.description,
        session_time=yoga_sessions.session_time,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(yoga_sessions)
    db.commit()
    db.refresh(yoga_sessions)
    return {"message": "YogaSessions created successfully", "data": yoga_sessions}


@router.get("/{id}")
async def get_yoga_sessions(id: int, db: db_dependency):
    yoga_sessions = db.query(YogaSessions).filter(YogaSessions.id == id).first()
    if yoga_sessions is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaSessions does not exist")
    return yoga_sessions


@router.put("/update/{id}")
async def update_yoga_sessions(id: int, yoga_sessions: YogaSessionsUpdate, db: db_dependency):
    check_yoga_sessions = db.query(YogaSessions).filter(YogaSessions.id == id).first()
    if check_yoga_sessions is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaSessions does not exist")
    # Define the update values in a dictionary
    # update_values = {
    #     "name": yoga_sessions.name,
    #     "price": yoga_sessions.price,
    #     "number_of_classes": yoga_sessions.number_of_classes,
    #     "description": yoga_sessions.description,
    #     "session_time": yoga_sessions.session_time,
    #     "updated_at": datetime.now(),
    # }
    # yoga_sessions = db.query(YogaSessions).filter(YogaSessions.id == id).update(update_values)
    if yoga_sessions.name:
        check_yoga_sessions.name = yoga_sessions.name
    if yoga_sessions.price:
        check_yoga_sessions.price = yoga_sessions.price
    if yoga_sessions.description:
        check_yoga_sessions.description = yoga_sessions.description
    if yoga_sessions.session_time:
        check_yoga_sessions.session_time = yoga_sessions.session_time
    if yoga_sessions.number_of_classes:
        check_yoga_sessions.number_of_classes = yoga_sessions.number_of_classes
    check_yoga_sessions.updated_at = datetime.now()
    db.commit()
    return {"message": "YogaSessions updated successfully"}


@router.delete("/delete/{id}")
async def delete_yoga_sessions(id: int, db: db_dependency):
    check_yoga_sessions = db.query(YogaSessions).filter(YogaSessions.id == id).first()
    if check_yoga_sessions is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="YogaSessions does not exist")
    db.query(YogaSessions).filter(YogaSessions.id == id).delete()
    db.commit()
    return {"message": "YogaSessions deleted successfully"}
