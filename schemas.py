from datetime import datetime, time
from typing import Optional, List

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
    description: str
    session_time: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class YogaSessionsUpdate(BaseModel):
    name: Optional[str]
    price: Optional[int]
    description: Optional[str]
    session_time: Optional[str]


class MembershipBookingsCreate(BaseModel):
    password: str
    yoga_session_id: int
    billing_names: str
    billing_email: str
    billing_address: str
    billing_city: str
    billing_country_id: int
    starting_date: str
    # booking_status: str
    # payment_status: str