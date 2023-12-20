from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import db_dependency
from starlette import status
from models import YogaClassBooking, User, MembershipBookings
from schemas import YogaClassBookingCreate
from typing import List, Optional, Annotated

router = APIRouter(
    tags=["YogaClassBooking"],
    prefix='/yoga_class_booking'
)

SECRET_KEY = 'a0ca9d98526e3a3d00cd899a53994e9a574fdecef9abe8bc233b1c262753cd2a'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password: str):
    return bcrypt_context.hash(password)


@router.get("/list")
async def get_yoga_class_booking(db: db_dependency):
    yoga_class_booking_list = db.query(YogaClassBooking).all()
    return yoga_class_booking_list


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_yoga_class_booking(yoga_class_booking: YogaClassBookingCreate, db: db_dependency):
    if yoga_class_booking.password == "":
        user = db.query(User).filter(User.email == yoga_class_booking.billing_email).first()
        membership_bookings = MembershipBookings(
            user_id=user.id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            billing_country_id=yoga_class_booking.billing_country_id,
            billing_names=yoga_class_booking.billing_names,
            billing_email=yoga_class_booking.billing_email,
            billing_address=yoga_class_booking.billing_address,
            billing_city=yoga_class_booking.billing_city,
            payment_status="paid",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(membership_bookings)
        yoga_class_booking = YogaClassBooking(
            user_id=user.id,
            yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            booking_date=yoga_class_booking.booking_date,
            booking_slot_time=yoga_class_booking.booking_slot_time,
            booking_slot_number=yoga_class_booking.booking_slot_number,
            booking_status="Pending",
            payment_status="Pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(yoga_class_booking)
        db.commit()
        return {"message": "Yoga Class Booking created successfully"}

    else:
        hashed_password = get_hashed_password(yoga_class_booking.password)
        user = User(
            name=yoga_class_booking.billing_names,
            email=yoga_class_booking.billing_email,
            username=yoga_class_booking.billing_email,
            password=hashed_password,
            role="user",
            created_at=datetime.now(),
            is_active=True,
        )
        db.add(user)
        db.commit()
        membership_bookings = MembershipBookings(
            user_id=user.id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            billing_country_id=yoga_class_booking.billing_country_id,
            billing_names=yoga_class_booking.billing_names,
            billing_email=yoga_class_booking.billing_email,
            billing_address=yoga_class_booking.billing_address,
            billing_city=yoga_class_booking.billing_city,
            payment_status="paid",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(membership_bookings)
        yoga_class_booking = YogaClassBooking(
            user_id=user.id,
            yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            booking_date=yoga_class_booking.booking_date,
            booking_slot_time=yoga_class_booking.booking_slot_time,
            booking_slot_number=yoga_class_booking.booking_slot_number,
            booking_status="Pending",
            payment_status="Pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(yoga_class_booking)
        db.commit()
        db.refresh(membership_bookings)

        return {"message": "Yoga Class Booking created successfully"}


@router.get("/spot_available")
async def get_spot_available(yoga_session_id: int, booking_date: str, booking_slot_time: str, yoga_class_location_id: int,  db: db_dependency):
    yoga_class_booking = db.query(YogaClassBooking).filter(YogaClassBooking.yoga_class_location_id == yoga_class_location_id).filter(YogaClassBooking.yoga_session_id == yoga_session_id).filter(
        YogaClassBooking.booking_date == booking_date).filter(YogaClassBooking.booking_slot_time == booking_slot_time).all()

    sum_slots = 0
    for booking in yoga_class_booking:
        sum_slots += booking.booking_slot_number  # Add each booking_slot_number to the sum_slots

    if sum_slots < 10:
        return {"message": {10 - sum_slots}}
    else:
        return {"message": "Spot not available"}
