from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import db_dependency
from starlette import status
from models import YogaClassBooking, User, MembershipBookings, YogaSessions, Country
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
    booking_info = []

    for booking in yoga_class_booking_list:
        user = db.query(User).filter(User.id == booking.user_id).first()
        yoga_session = db.query(YogaSessions).filter(YogaSessions.id == booking.yoga_session_id).first()

        data = {
            "id": booking.id,
            "user": {
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "gender": user.gender,
            },
            "yoga_session": yoga_session,
            "booking": booking,
            # Include other booking details as needed
        }
        booking_info.append(data)

    return booking_info


@router.get("/user_bookings")
async def get_membership_bookings(user_id: int, db: db_dependency):
    # if db.query(MembershipBookings).filter(MembershipBookings.id == user_id).first() is None:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Membership Bookings does not exist")

    # yoga_session = db.query(YogaClassBooking).filter(YogaClassBooking.user_id == user_id).first().yoga_session
    # user_info = db.query(YogaClassBooking).filter(YogaClassBooking.user_id == user_id).first().user
    # user_data = []
    # data = {
    #     "name": user_info.name,
    #     "email": user_info.email,
    #     "phone_number": user_info.phone_number,
    #     "gender": user_info.gender,
    #     "yoga_session": yoga_session,
    #     "booking": db.query(YogaClassBooking).filter(YogaClassBooking.user_id == user_id).first()
    # }
    # user_data.append(data)
    # return data

    yoga_class_booking_list = db.query(YogaClassBooking).filter(YogaClassBooking.user_id == user_id).all()
    booking_info = []

    for booking in yoga_class_booking_list:
        user = db.query(User).filter(User.id == booking.user_id).first()
        yoga_session = db.query(YogaSessions).filter(YogaSessions.id == booking.yoga_session_id).first()

        data = {
            "id": booking.id,
            "user": {
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "gender": user.gender,
            },
            "yoga_session": yoga_session,
            "booking": booking,
            # Include other booking details as needed
        }
        booking_info.append(data)

    return booking_info


@router.get("/transaction")
async def get_transaction(user_id: int, db: db_dependency):
    membership_bookings = db.query(MembershipBookings).filter(MembershipBookings.user_id == user_id).all()
    transactions = []
    for transaction in membership_bookings:
        yoga_session = db.query(YogaSessions).filter(YogaSessions.id == transaction.yoga_session_id).first()
        country = db.query(Country).filter(Country.id == transaction.billing_country_id).first()
        data = {
            "id": transaction.id,
            "yoga_session": yoga_session.name,
            "country": country.name,
            "booking": transaction,
        }
        transactions.append(data)
    return transactions


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
        db.commit()
        yoga_class_booking = YogaClassBooking(
            user_id=user.id,
            yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            booking_date=yoga_class_booking.booking_date,
            booking_slot_time=yoga_class_booking.booking_slot_time,
            booking_slot_number=yoga_class_booking.booking_slot_number,
            transaction_id=membership_bookings.id,
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
        db.commit()

        yoga_class_booking = YogaClassBooking(
            user_id=user.id,
            yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            booking_date=yoga_class_booking.booking_date,
            booking_slot_time=yoga_class_booking.booking_slot_time,
            booking_slot_number=yoga_class_booking.booking_slot_number,
            transaction_id=membership_bookings.id,
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
async def get_spot_available(yoga_session_id: int, booking_date: str, booking_slot_time: str,
                             yoga_class_location_id: int, db: db_dependency):
    yoga_class_booking = db.query(YogaClassBooking).filter(
        YogaClassBooking.yoga_class_location_id == yoga_class_location_id).filter(
        YogaClassBooking.yoga_session_id == yoga_session_id).filter(
        YogaClassBooking.booking_date == booking_date).filter(
        YogaClassBooking.booking_slot_time == booking_slot_time).all()

    sum_slots = 0
    for booking in yoga_class_booking:
        sum_slots += booking.booking_slot_number  # Add each booking_slot_number to the sum_slots

    if sum_slots < 10:
        return {"message": {10 - sum_slots}}
    else:
        return {"message": "Spot not available"}


@router.get("/count")
async def get_count(user_id: int, db: db_dependency):
    count_yoga_class_bookings = db.query(YogaClassBooking).filter(YogaClassBooking.user_id == user_id).filter(
        YogaClassBooking.booking_status == "Pending").count()
    sum_membership_bookings = db.query(MembershipBookings).filter(MembershipBookings.user_id == user_id).all()
    sum = 0
    for i in sum_membership_bookings:
        price = int(i.yoga_session.price)
        sum += price
    return {"count": count_yoga_class_bookings, "sum": sum}
