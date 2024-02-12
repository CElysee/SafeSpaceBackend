from datetime import time

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), unique=True, index=True)
    phone_number = Column(String(50), nullable=True)
    name = Column(String(50))
    username = Column(String(50), unique=True, index=True)
    password = Column(String(250))
    role = Column(String(50), nullable=False)
    gender = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    registrations_referred_by = Column(String(50), nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    last_login = Column(DateTime)
    deleted = Column(Boolean)

    country = relationship("Country", back_populates="user")
    membership_bookings = relationship("MembershipBookings", back_populates="user")
    yoga_class_booking = relationship("YogaClassBooking", back_populates="user")


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    code = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user = relationship("User", back_populates="country")
    membership_bookings = relationship("MembershipBookings", back_populates="country")


class YogaSessions(Base):
    __tablename__ = "yoga_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    price = Column(String(50))
    description = Column(Text)
    session_time = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    membership_bookings = relationship("MembershipBookings", back_populates="yoga_session")
    yoga_class_booking = relationship("YogaClassBooking", back_populates="yoga_session")


class MembershipBookings(Base):
    __tablename__ = "membership_bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    yoga_session_id = Column(Integer, ForeignKey("yoga_sessions.id"))
    billing_names = Column(String(50))
    billing_email = Column(String(50))
    billing_phone_number = Column(String(50))
    billing_address = Column(String(50))
    billing_city = Column(String(50))
    billing_country_id = Column(Integer, ForeignKey("countries.id"))
    transaction_amount = Column(String(50))
    payment_status = Column(String(50))
    transaction_token = Column(String(100))
    transaction_ref = Column(String(100))
    transaction_id = Column(String(100))
    currency = Column(String(50))
    CCDapproval = Column(String(50))
    PnrID = Column(String(50))
    CompanyRef = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user = relationship("User", back_populates="membership_bookings")
    yoga_session = relationship("YogaSessions", back_populates="membership_bookings")
    country = relationship("Country", back_populates="membership_bookings")
    yoga_class_booking = relationship("YogaClassBooking", back_populates="membership_bookings")


class YogaClassLocation(Base):
    __tablename__ = "yoga_class_location"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    address = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # yoga_class_booking = relationship("YogaClassBooking", back_populates="yoga_class_location")


class YogaClassBooking(Base):
    __tablename__ = "yoga_class_booking"

    id = Column(Integer, primary_key=True, index=True)
    session_ref = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))
    # yoga_class_location_id = Column(Integer, ForeignKey("yoga_class_location.id"))
    yoga_class_location_id = Column(String(50))
    yoga_session_id = Column(Integer, ForeignKey("yoga_sessions.id"))
    transaction_id = Column(Integer, ForeignKey("membership_bookings.id"))
    booking_date = Column(DateTime)
    booking_slot_time = Column(String(50))
    booking_slot_number = Column(Integer)
    booking_status = Column(String(50))
    payment_status = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user = relationship("User", back_populates="yoga_class_booking")
    # yoga_class_location = relationship("YogaClassLocation", back_populates="yoga_class_booking")
    yoga_session = relationship("YogaSessions", back_populates="yoga_class_booking")
    membership_bookings = relationship("MembershipBookings", back_populates="yoga_class_booking")
