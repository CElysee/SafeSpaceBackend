from datetime import datetime, time
from typing import Optional, List, Text

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    name: str
    email: EmailStr
    username: Optional[str]
    password: str
    role: str
    gender: str
    registrations_referred_by: str
    phone_number: Optional[str]
    country_id: Optional[int]

    # last_login: Optional[datetime] = None
    # deleted: Optional[bool] = False

    class Config:
        from_attributes = True


class UserCreate(User):
    pass


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str
    username: str
    role: str
    created_at: datetime
    is_active: bool
    # country_id: int
    # user_profile_id: int


class UserCheck(BaseModel):
    email: EmailStr
    session_name: str


class UserId(BaseModel):
    id: int


class CountryBase(BaseModel):
    name: str
    code: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class CountryUpdate(CountryBase):
    pass


class CountryOut(CountryBase):
    id: int

    class Config:
        from_attributes = True


class YogaSessionsCreate(BaseModel):
    name: str
    price: int
    number_of_classes: int
    description: str
    session_time: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class YogaSessionsUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[str] = None
    number_of_classes: Optional[int] = None
    description: Optional[str] = None
    session_time: Optional[str] = None


class MembershipBookingsCreate(BaseModel):
    password: str
    yoga_session_id: int
    billing_names: str
    billing_email: str
    billing_phone_number: str
    billing_address: str
    billing_city: str
    billing_country_id: int
    starting_date: str
    # booking_status: str
    # payment_status: str


class YogaClassLocationCreate(BaseModel):
    name: str
    address: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class YogaClassLocationUpdate(BaseModel):
    name: Optional[str]
    address: Optional[str]


class YogaClassBookingCreate(BaseModel):
    password: str
    yoga_session_id: int
    yoga_session_name: str
    session_ref: str
    billing_names: str
    billing_email: str
    billing_address: str
    billing_phone_number: str
    billing_city: str
    billing_country_id: int
    # user_id: int
    yoga_session_id: int
    yoga_class_location_id: str
    booking_date: str
    booking_slot_time: str
    booking_more_sessions: List[str]
    payment_package_id: int
    # booking_slot_number: Optional[int]
    # booking_status: str
    # payment_status: str


class PaymentDetails(BaseModel):
    amount: str
    serviceDescription: str
    # serviceDate: str


class SessionCreditsCreate(BaseModel):
    user_id: int
    remaining_credits: str
    session_class_name: str
