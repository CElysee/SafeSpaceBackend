from datetime import datetime, timedelta
import calendar
import random
from typing import Annotated, Any, List
from sqlalchemy import select
from fastapi import APIRouter, HTTPException, Depends, UploadFile, Form, File
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from starlette import status

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

import models
import schemas
from database import SessionLocal
import logging
import os
import uuid
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader
from email.mime.image import MIMEImage
import requests

router = APIRouter(
    tags=["Auth"],
    prefix='/auth'
)

load_dotenv()  # Load environment variables from .env

SECRET_KEY = 'a0ca9d98526e3a3d00cd899a53994e9a574fdecef9abe8bc233b1c262753cd2a'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token ')
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def get_user_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception


def authenticated_user(username: str, password: str, db):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", )
    if not bcrypt_context.verify(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", )
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta, email: str, role: str):
    encode = {'sub': username, 'id': user_id, 'email': email, 'role': role}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_hashed_password(password: str):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def get_user_by_email(email: str, password: str, db: Session):
    query = db.query(models.User).filter(models.User.email == email)
    user = query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", )
    if not bcrypt_context.verify(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password", )
    user.last_login = datetime.now()
    db.commit()
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        user = db.query(models.User).filter(models.User.username == username).first()
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        # return {'username': username, 'id': user_id, 'user_role': user_role}
        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")


async def get_current_active_user(
        current_user: Annotated[schemas.UserOut, Depends(get_current_user)]
):
    return current_user


user_dependency = Annotated[dict, Depends(get_current_user)]


class Token(BaseModel):
    access_token: str
    token_type: str
    # role: str


class UserToken(BaseModel):
    access_token: str
    token_type: str
    role: str
    userId: int
    userData: dict


UPLOAD_FOLDER = "CarSellImages"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def save_uploaded_file(file: UploadFile):
    file_extension = file.filename.split(".")[-1]
    random_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, random_filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return random_filename


def read_email_template():
    template_path = os.path.join(os.getcwd(), "templates", "email", "email.html")
    with open(template_path, "r") as file:
        return file.read()


def send_sms(phone_number, message):
    url = 'https://api.mista.io/sms'
    api_key = os.getenv('386|hY4eAWqZdbXnMOccURnsvdkPF6myOZENEU7GPhOY ')
    sender_id = os.getenv('KIVUFEST')

    headers = {
        'x-api-key': api_key
    }
    payload = {
        'to': phone_number,
        'from': sender_id,
        'unicode': '0',
        'sms': message,
        'action': 'send-sms'
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(response)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def generate_random_mixed():
    random_number = random.randint(10, 9999)
    return random_number


@router.get('/all')
async def all_users(db: db_dependency):
    # all_users = db.query(models.User).all()
    all_users = db.query(models.User).order_by(models.User.id.desc()).all()

    users = []
    for user in all_users:
        last_login = None
        if user.last_login:
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M:%S')
        results = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
            "account_status": user.is_active,
            "last_login": last_login,
            "role": user.role,
            "created_at": user.created_at,
        }
        users.append(results)
    return users


@router.post('/verify_phone_number')
async def verify_phone_number(phone_number: str, db: db_dependency):
    new_phone = "+250" + phone_number
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if user:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Phone number already exist")
    else:
        return send_sms(new_phone, f"Your verification code is {generate_random_mixed}")
        # return {"message": "Verification code sent successfully"}


@router.post("/users/create", status_code=status.HTTP_201_CREATED)
async def create_user(db: Session = Depends(get_db), user_request: schemas.UserCreate = Depends()):
    check_user = db.query(models.User).filter(models.User.email == user_request.email).first()
    chech_username = db.query(models.User).filter(models.User.username == user_request.username).first()
    if check_user:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Email already exist")
    if chech_username:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Username already exist")
    try:
        hashed_password = get_hashed_password(user_request.password)
        new_user = models.User(
            username=user_request.username,
            email=user_request.email,
            name=user_request.name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            password=hashed_password,
            role=user_request.role,
            gender=user_request.gender,
            registrations_referred_by=user_request.registrations_referred_by,
            country_id=user_request.country_id,
            phone_number=user_request.phone_number,
            is_active=True
        )
        db.add(new_user)
        db.commit()

        # smtp_server = os.getenv("MAILGUN_SMTP_SERVER")
        # smtp_port = int(os.getenv("MAILGUN_SMTP_PORT"))
        # smtp_username = os.getenv("MAILGUN_SMTP_USERNAME")
        # smtp_password = os.getenv("MAILGUN_SMTP_PASSWORD")
        #
        # # Read the email template
        # email_template_content = read_email_template()
        #
        # # Create a Jinja2 environment and load the template
        # env = Environment(loader=FileSystemLoader(os.path.join(os.getcwd(), "templates", "email")))
        # template = env.from_string(email_template_content)
        #
        # message = "We are absolutely thrilled to welcome you to our vibrant community! Your registration has been confirmed, and we're excited to have you on board. \n At Mentor.rw, we believe in fostering a supportive and engaging environment where members like you can connect, learn, and collaborate. Your presence adds immense value to our community, and we can't wait to see the positive impact we'll create together."
        # # Render the template with the provided data
        # email_content = template.render(message=message, name=user_request.name)
        #
        # # Create the email content
        # email = EmailMessage()
        # email["From"] = f"Mentor.rw <{smtp_username}>"
        # email["To"] = user_request.email
        # email["Subject"] = "Welcome to Mentor Community - Registration is Completed 🎉"
        # email.set_content("This is the plain text content.")
        # email.add_alternative(email_content, subtype="html")
        # # Attach the image
        # image_path = "templates/email/mentorlogo.png"
        # with open(image_path, "rb") as img_file:
        #     image = MIMEImage(img_file.read())
        #     image.add_header("Content-ID", "mentorlogo.png")
        #     email.attach(image)
        #
        # # Connect to the SMTP server and send the email
        # with smtplib.SMTP(smtp_server, smtp_port) as server:
        #     server.starttls()
        #     server.login(smtp_username, smtp_password)
        #     server.send_message(email)

        return {"message": "User created successfully"}

    except Exception as e:
        db.rollback()
        error_msg = f"Error adding a new user: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticated_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

    token = create_access_token(user.username, user.id, timedelta(minutes=60), user.email, user.role)

    return {'message': "Successfully Authenticated", 'access_token': token, 'token_type': 'bearer'}


@router.post("/login", response_model=UserToken)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    # user = authenticated_user(form_data.username, form_data.password, db)
    user = get_user_by_email(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token = create_access_token(user.username, user.id, timedelta(minutes=60), user.email, user.role)
    user_info = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone_number": user.phone_number,
        "username": user.username,
        "role": user.role,
    }
    return {'access_token': token, 'token_type': 'bearer', 'role': user.role, 'userId': user.id, 'userData': user_info}


# User info by id
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    country = user.country
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone_number": user.phone_number,
        "username": user.username,
        "role": user.role,
        "gender": user.gender,
        "country": country,
    }
    return data


@router.post("/check_username", status_code=status.HTTP_200_OK)
async def check_username(user_request: schemas.UserCheck, db: db_dependency):
    user = db.query(models.User).filter(models.User.email == user_request.email).first()
    check_credits = db.query(models.SessionCredits).filter(
        models.SessionCredits.user_id == user.id,
        models.SessionCredits.session_class_name == user_request.session_name
    ).first()
    remaining_credits = 0
    if check_credits:
        remaining_credits = check_credits.remaining_credits

    if user is None:
        return {'message': "Email not registered"}
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not yet Approved")
    elif user:
        country_details = user.country
        details = {
            "name": user.name,
            "phone_number": user.phone_number,
            "country": country_details,
            "credits": remaining_credits
        }
        return {"message": "Account is registered", "data": details}


@router.get("/users/me", response_model=schemas.UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/billing_info")
async def get_billing_info(user_id: int, db: db_dependency):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_country = user.country
    user_membership = db.query(models.MembershipBookings).filter(models.MembershipBookings.user_id == user_id).first()
    if not user_membership:
        raise HTTPException(status_code=404, detail="User membership not found")
    user_membership = {
        "billing_names": user_membership.billing_names,
        "billing_email": user_membership.billing_email,
        "billing_phone_number": user_membership.billing_phone_number,
        "billing_address": user_membership.billing_address,
        "billing_city": user_membership.billing_city,
        "billing_country": user_country,
        "billing_country_id": user_membership.billing_country_id,
    }
    return user_membership


@router.post("/users/profile/update", status_code=status.HTTP_200_OK)
async def update_profile(
        name: str = Form(None),
        email: str = Form(None),
        phone_number: str = Form(None),
        gender: str = Form(None),
        user_id: str = Form(...),
        country_id: int = Form(None),
        db: Session = Depends(get_db),
):
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Update user and user profile fields
        if name:
            user.name = name
        if email:
            user.email = email
        if phone_number:
            user.phone_number = phone_number
        if country_id:
            user.country_id = country_id
        if gender:
            user.gender = gender  # Assuming you intended to update the country field

        # Commit the changes to the database
        db.commit()

        return {"message": "Profile updated successfully"}

    except Exception as e:
        db.rollback()  # Rollback the transaction in case of an exception
        raise HTTPException(status_code=500, detail="Error updating user profile")

    finally:
        db.close()


@router.post("/users/profile/update_password", status_code=status.HTTP_200_OK)
async def update_password(
        old_password: str = Form(...),
        new_password: str = Form(...),
        user_id: str = Form(...),
        db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if old_password and new_password:
        if not bcrypt_context.verify(old_password, user.password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        else:
            user.password = get_hashed_password(new_password)
            # Commit the changes to the database
            db.commit()
            return {"message": "Password updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
