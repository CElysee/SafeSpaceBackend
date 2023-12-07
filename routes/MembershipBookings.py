from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import db_dependency
from starlette import status
from models import MembershipBookings
from typing import List, Optional, Annotated
from schemas import MembershipBookingsCreate
from passlib.context import CryptContext

router = APIRouter(
    tags=["MembershipBookings"],
    prefix='/membership_bookings'
)

SECRET_KEY = 'a0ca9d98526e3a3d00cd899a53994e9a574fdecef9abe8bc233b1c262753cd2a'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password: str):
    return bcrypt_context.hash(password)


@router.get("/list")
async def get_membership_bookings(db: db_dependency):
    membership_bookings_list = db.query(MembershipBookings).all()
    booking_info = []

    for booking in membership_bookings_list:
        user = db.query(models.User).filter(models.User.id == booking.user_id).first()
        yoga_session = db.query(models.YogaSessions).filter(models.YogaSessions.id == booking.yoga_session_id).first()
        country = db.query(models.Country).filter(models.Country.id == booking.billing_country_id).first()

        data = {
            "id": booking.id,
            "user": {
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "gender": user.gender,
            },
            "yoga_session": yoga_session,
            "country": country.name,
            "booking": booking,
            # Include other booking details as needed
        }
        booking_info.append(data)

    return booking_info


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_membership_bookings(membership_bookings: MembershipBookingsCreate, db: db_dependency):
    if membership_bookings.password == "":
        user = db.query(models.User).filter(models.User.email == membership_bookings.billing_email).first()
        membership_bookings = MembershipBookings(
            user_id=user.id,
            yoga_session_id=membership_bookings.yoga_session_id,
            billing_country_id=membership_bookings.billing_country_id,
            billing_names=membership_bookings.billing_names,
            billing_email=membership_bookings.billing_email,
            billing_address=membership_bookings.billing_address,
            billing_city=membership_bookings.billing_city,
            starting_date=membership_bookings.starting_date,
            booking_status="pending",
            payment_status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(membership_bookings)
        db.commit()
        db.refresh(membership_bookings)
        return {"message": "Membership Bookings created successfully"}

    else:
        hashed_password = get_hashed_password(membership_bookings.password)
        user = models.User(
            name=membership_bookings.billing_names,
            email=membership_bookings.billing_email,
            username=membership_bookings.billing_email,
            password=hashed_password,
            role="user",
            created_at=datetime.now(),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        membership_bookings = MembershipBookings(
            user_id=user.id,
            yoga_session_id=membership_bookings.yoga_session_id,
            billing_country_id=membership_bookings.billing_country_id,
            billing_names=membership_bookings.billing_names,
            billing_email=membership_bookings.billing_email,
            billing_address=membership_bookings.billing_address,
            billing_city=membership_bookings.billing_city,
            starting_date=membership_bookings.starting_date,
            booking_status="pending",
            payment_status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(membership_bookings)
        db.commit()
        db.refresh(membership_bookings)
        return {"message": "Membership Bookings created successfully"}


@router.get("/{id}")
async def get_membership_bookings(id: int, db: db_dependency):
    if db.query(MembershipBookings).filter(MembershipBookings.id == id).first() is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership Bookings does not exist")
    yoga_session = db.query(MembershipBookings).filter(MembershipBookings.id == id).first().yoga_session
    country = db.query(MembershipBookings).filter(MembershipBookings.id == id).first().country
    user_data = []
    user_info = db.query(MembershipBookings).filter(MembershipBookings.id == id).first().user
    data = {
        "name": user_info.name,
        "email": user_info.email,
        "phone_number": user_info.phone_number,
        "gender": user_info.gender,
        "country": country,
        "yoga_session": yoga_session,
        "booking": db.query(MembershipBookings).filter(MembershipBookings.id == id).first()
    }
    user_data.append(data)
    return data


@router.get("/user/{id}")
async def get_membership_bookings(id: int, db: db_dependency):
    membership_bookings_list = db.query(MembershipBookings).filter(MembershipBookings.user_id == id).all()
    booking_info = []

    for booking in membership_bookings_list:
        user = db.query(models.User).filter(models.User.id == booking.user_id).first()
        yoga_session = db.query(models.YogaSessions).filter(models.YogaSessions.id == booking.yoga_session_id).first()
        country = db.query(models.Country).filter(models.Country.id == booking.billing_country_id).first()

        data = {
            "id": booking.id,
            "user": {
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "gender": user.gender,
            },
            "yoga_session": yoga_session,
            "country": country.name,
            "booking": booking,
            # Include other booking details as needed
        }
        booking_info.append(data)
    return booking_info


@router.delete("/delete/{id}")
async def delete_membership_bookings(id: int, db: db_dependency):
    check_membership_bookings = db.query(MembershipBookings).filter(MembershipBookings.id == id).first()
    if check_membership_bookings is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership Bookings does not exist")
    db.query(MembershipBookings).filter(MembershipBookings.id == id).delete()
    db.commit()
    return {"message": "Membership Bookings deleted successfully"}


# count booking by user and sum price
@router.get("/count/{id}")
async def count_membership_bookings(id: int, db: db_dependency):
    count_membership_bookings = db.query(MembershipBookings).filter(MembershipBookings.user_id == id).count()
    sum_membership_bookings = db.query(MembershipBookings).filter(MembershipBookings.user_id == id).all()
    sum = 0
    for i in sum_membership_bookings:
        price = int(i.yoga_session.price)
        sum += price
    return {"count": count_membership_bookings, "sum": sum}
