import os
import random
import smtplib
import string
from datetime import datetime
from email.mime.image import MIMEImage

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import models
from database import db_dependency
from starlette import status
from models import YogaClassBooking, User, MembershipBookings, YogaSessions, Country, SessionCredits
from schemas import YogaClassBookingCreate, PaymentDetails
from typing import List, Optional, Annotated
from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage
import requests
import xml.etree.ElementTree as ET

router = APIRouter(
    tags=["YogaClassBooking"],
    prefix='/yoga_class_booking'
)

SECRET_KEY = 'a0ca9d98526e3a3d00cd899a53994e9a574fdecef9abe8bc233b1c262753cd2a'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
load_dotenv()  # Load environment variables from .env


def get_hashed_password(password: str):
    return bcrypt_context.hash(password)


def formatted_date(date_input):
    current_year = datetime.now().year
    input_date = datetime.strptime(date_input + f" {current_year}", "%A %B %d %Y")
    # Format the date in the desired format
    formatted_date = input_date.strftime("%Y-%m-%d 00:00:00")

    return formatted_date


def read_email_template_booking():
    template_path = os.path.join(os.getcwd(), "templates", "email", "email.html")
    with open(template_path, "r") as file:
        return file.read()


def read_email_custom_template_booking():
    template_path = os.path.join(os.getcwd(), "templates", "email", "AdvancedEmail.html")
    with open(template_path, "r") as file:
        return file.read()


def DPO_payment_request(billing_country, session_amount, first_name, last_name, receiver_address, receiver_city,
                        receiver_email, billing_number, db: Session,
                        membership_bookings: MembershipBookings):
    contry_code = db.query(models.Country).filter(models.Country.id == billing_country).first()
    currency = "RWF"
    company_ref = "0"
    redirect_url = os.getenv("DPO_REDIRECT_URL")
    back_url = ""
    service_description = "Yoga class session booking"
    service_date = datetime.now().strftime('%Y/%m/%d %H:%M')
    customerCountry = contry_code.code
    DefaultPayment = "MO"

    url = os.getenv("DPO_ENDPOINT")
    dpo_company_token = os.getenv("DPO_COMPANY_TOKEN")
    services_code = os.getenv("DPO_SERVICE_CODE")
    xml = f'''<?xml version="1.0" encoding="utf-8"?>
                          <API3G>
                            <CompanyToken>{dpo_company_token}</CompanyToken>
                            <Request>createToken</Request>
                            <Transaction>
                              <PaymentAmount>{session_amount}</PaymentAmount>
                              <PaymentCurrency>{currency}</PaymentCurrency>
                              <CompanyRef>{company_ref}</CompanyRef>
                              <RedirectURL>{redirect_url}</RedirectURL>
                              <BackURL>{back_url}</BackURL>
                              <CompanyRefUnique>{company_ref}</CompanyRefUnique>
                              <customerFirstName>{first_name}</customerFirstName>
                              <customerLastName>{last_name}</customerLastName>
                              <customerAddress>{receiver_address}</customerAddress>
                              <customerCity>{receiver_city}</customerCity>
                              <customerCountry>{customerCountry}</customerCountry>
                              <customerPhone>{billing_number}</customerPhone>
                              <customerEmail>{receiver_email}</customerEmail>
                              <DefaultPayment>{DefaultPayment}</DefaultPayment>
                              <DefaultPaymentCountry>rwanda</DefaultPaymentCountry>
                              <PTL>5</PTL>
                            </Transaction>
                            <Services>
                              <Service>
                                <ServiceType>{services_code}</ServiceType>
                                <ServiceDescription>{service_description}</ServiceDescription>
                                <ServiceDate>{service_date}</ServiceDate>
                              </Service>
                            </Services>
                          </API3G>'''
    headers = {'Content-Type': 'application/xml'}
    # r = requests.post(url, data=xml, headers=headers)
    try:
        response_payment = requests.post(url, data=xml, headers=headers)
        response_payment.raise_for_status()  # Raise an exception for bad responses (4xx, 5xx)
        xml_response = response_payment.text
        print(f"Response Status Code: {response_payment.status_code}")
        print(f"Response Content: {response_payment.text}")
        # Parse XML
        root = ET.fromstring(xml_response)
        # Convert XML to dictionary
        result_data = {}
        for child in root:
            result_data[child.tag] = child.text

        if result_data['Result'] == "000":
            trans_token = result_data['TransToken']
            trans_ref = result_data['TransRef']
            trans_message = result_data['ResultExplanation']
            redirection_url = f"https://secure.3gdirectpay.com/payv2.php?ID={trans_token}"
            membership_bookings_transaction = db.query(MembershipBookings).filter(
                MembershipBookings.id == membership_bookings.id).first()
            membership_bookings_transaction.transaction_token = trans_token
            membership_bookings_transaction.transaction_ref = trans_ref
            membership_bookings_transaction.CompanyRef = company_ref
            membership_bookings_transaction.currency = currency
            db.commit()
            return {"message": "Transaction created", "status_code": result_data['Result'],
                    "redirection_url": redirection_url}
        else:
            return {"message": result_data['ResultExplanation'], "status_code": result_data['Result']}
    except requests.exceptions.RequestException as e:
        # Handle request exceptions (connection errors, timeouts, etc.)
        return {"error": str(e)}
    # return {"message": "Yoga Class Booking created successfully"}


def create_membership_bookings(yoga_class_booking, user, session_amount, billing_number, db: Session):
    membership_bookings = MembershipBookings(
        user_id=user.id,
        yoga_session_id=yoga_class_booking.yoga_session_id,
        billing_country_id=yoga_class_booking.billing_country_id,
        billing_names=yoga_class_booking.billing_names,
        billing_email=yoga_class_booking.billing_email,
        billing_phone_number=billing_number,
        billing_address=yoga_class_booking.billing_address,
        billing_city=yoga_class_booking.billing_city,
        transaction_amount=session_amount,
        payment_status="Pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(membership_bookings)
    db.commit()
    return membership_bookings


def create_new_yoga_class_booking(yoga_class_booking, user, formatted_session_date, membership_bookings_id,
                                  db: Session):
    yoga_class_booking = YogaClassBooking(
        user_id=user.id,
        session_ref=yoga_class_booking.session_ref,
        yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
        yoga_session_name=yoga_class_booking.yoga_session_name,
        yoga_session_id=yoga_class_booking.yoga_session_id,
        booking_date=formatted_session_date,
        booking_slot_time=yoga_class_booking.booking_slot_time,
        # booking_slot_number=yoga_class_booking.booking_slot_number,
        transaction_id=membership_bookings_id,
        booking_status="Pending",
        payment_status="Pending",
        mode_of_payment="Momo/Card",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(yoga_class_booking)
    db.commit()
    return yoga_class_booking


def create_session_credits(user, session_class_name, session_package_info, more_session_array, db):
    if session_package_info.name in ["5 CLASSES PASS", "10 CLASSES PASS", "SADHANA 4 CLASSES PASS"]:
        number_of_classes = session_package_info.number_of_classes
        booked_classes = len(more_session_array)
        remaining_classes = number_of_classes - (booked_classes + 1)

        if remaining_classes > 0:
            current_credits = db.query(SessionCredits).filter(SessionCredits.user_id == user.id).first()
            if current_credits and session_class_name == current_credits.session_class_name:
                session_current_credits = int(current_credits.remaining_credits)
                current_credits.remaining_credits = str(int(remaining_classes) + session_current_credits)
                db.commit()
                return current_credits
            else:
                # Create new session credits if not found or if session_class_name does not match
                new_session_credits = SessionCredits(
                    user_id=user.id,
                    remaining_credits=remaining_classes,
                    session_class_name=session_class_name,
                    created_at=datetime.now()
                )
                db.add(new_session_credits)
                db.commit()
                return new_session_credits


def deduct_session_credits(user, session_class_name, session_package_info, more_session_array, db: Session):
    # Check if the session package is eligible for deduction
    booked_classes = len(more_session_array)
    remaining_classes = booked_classes + 1
    # Ensure there are remaining classes to deduct credits
    if remaining_classes > 0:
        # Query current session credits for the user and class
        check_current_credits = (
            db.query(SessionCredits)
            .filter(SessionCredits.user_id == user.id, SessionCredits.session_class_name == session_class_name)
            .first()
        )
        # If there are existing credits, deduct and update the database
        if check_current_credits:
            current_credits = int(check_current_credits.remaining_credits)
            updated_credits = max(0, current_credits - remaining_classes)
            check_current_credits.remaining_credits = str(updated_credits)
            db.commit()

            return updated_credits


def send_confirmation_email(booking_session_info, check_transaction, db: Session):
    subject = f"Booking Confirmation - SafeSpace Yoga Studio!"
    # message = f"Your scheduled yoga session with is confirmed for {booking_session_info.booking_date} at {booking_session_info.booking_slot_time}. You will receive an email if anything changes."
    smtp_server = os.getenv("MAILGUN_SMTP_SERVER")
    smtp_port = int(os.getenv("MAILGUN_SMTP_PORT"))
    smtp_username = os.getenv("MAILGUN_SMTP_USERNAME")
    smtp_password = os.getenv("MAILGUN_SMTP_PASSWORD")

    # Read the email template
    # email_template_content = read_email_template_booking()
    email_template_content = read_email_custom_template_booking()

    # Create a Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader(os.path.join(os.getcwd(), "templates", "email")))
    template = env.from_string(email_template_content)
    all_booking_sessions = db.query(models.YogaClassBooking).filter(
        models.YogaClassBooking.transaction_id == check_transaction.id).all()

    # Render the template with the provided data
    email_content = template.render(confirmation_code=check_transaction.transaction_ref,
                                    session_ref=booking_session_info.session_ref,
                                    session_amount=check_transaction.transaction_amount,
                                    name=check_transaction.billing_names,
                                    booking_date=booking_session_info.booking_date,
                                    booking_slot_time=booking_session_info.booking_slot_time,
                                    all_booking_sessions=all_booking_sessions,
                                    )

    # Create the email content
    email = EmailMessage()
    email["From"] = f"SafeSpaceYoga.rw <{smtp_username}>"
    email["To"] = check_transaction.billing_email
    # email["To"] = "ccelyse1@gmail.com"
    email["Subject"] = subject
    email.set_content("This is the plain text content.")
    email.add_alternative(email_content, subtype="html")
    # Attach the image
    image_path = "templates/email/logo.png"
    with open(image_path, "rb") as img_file:
        image = MIMEImage(img_file.read())
        image.add_header("Content-ID", "logo.png")
        email.attach(image)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(email)
    return {"message": "Payment status updated"}


def random_string_ref():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))


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
    receiver_name = yoga_class_booking.billing_names
    name_parts = receiver_name.split()
    # Extract the first and last names
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])
    receiver_email = yoga_class_booking.billing_email
    receiver_address = yoga_class_booking.billing_address
    receiver_city = yoga_class_booking.billing_city
    receiver_address = yoga_class_booking.billing_address
    formatted_session_date = formatted_date(yoga_class_booking.booking_date)
    billing_number = yoga_class_booking.billing_phone_number
    billing_country = yoga_class_booking.billing_country_id
    session_class_name = yoga_class_booking.yoga_session_name

    more_session_array = yoga_class_booking.booking_more_sessions
    length_of_session = len(more_session_array)
    session_package_info = db.query(models.YogaSessions).filter(
        models.YogaSessions.id == yoga_class_booking.yoga_session_id).first()
    session_amount = session_package_info.price

    if session_package_info.name == "DROP IN":
        new_amount = int(session_amount) * (length_of_session + 1)
        session_amount = new_amount

    if yoga_class_booking.password == "":
        user = db.query(User).filter(User.email == yoga_class_booking.billing_email).first()
        # Create user credits
        create_session_credits(user, session_class_name, session_package_info, more_session_array, db)
        # Create new membership booking
        mew_membership_bookings = create_membership_bookings(yoga_class_booking, user, session_amount, billing_number,
                                                             db)
        membership_bookings_id = mew_membership_bookings.id

        # Create new yoga booking

        new_yoga_class_booking = create_new_yoga_class_booking(yoga_class_booking, user, formatted_session_date,
                                                               membership_bookings_id, db)
        if more_session_array:
            for sessions_date in more_session_array:
                updated_date = formatted_date(sessions_date)
                yoga_class_booking = YogaClassBooking(
                    user_id=user.id,
                    session_ref=random_string_ref(),
                    yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
                    yoga_session_name=yoga_class_booking.yoga_session_name,
                    yoga_session_id=yoga_class_booking.yoga_session_id,
                    booking_date=updated_date,
                    booking_slot_time=yoga_class_booking.booking_slot_time,
                    # booking_slot_number=yoga_class_booking.booking_slot_number,
                    transaction_id=membership_bookings_id,
                    booking_status="Pending",
                    payment_status="Pending",
                    mode_of_payment="Momo/Card",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(yoga_class_booking)
                db.commit()

        # Initialize the payment request to DPO
        make_payment = DPO_payment_request(billing_country, session_amount, first_name, last_name, receiver_address,
                                           receiver_city, receiver_email, billing_number, db, mew_membership_bookings)
        return make_payment

    else:

        # Create new user account
        hashed_password = get_hashed_password(yoga_class_booking.password)
        user = User(
            name=yoga_class_booking.billing_names,
            email=yoga_class_booking.billing_email,
            phone_number=billing_number,
            username=yoga_class_booking.billing_email,
            country_id=yoga_class_booking.billing_country_id,
            password=hashed_password,
            role="user",
            created_at=datetime.now(),
            is_active=True,
        )
        db.add(user)
        db.commit()

        # Create user credits
        create_session_credits(user, session_class_name, session_package_info, more_session_array, db)
        # Create new membership booking
        mew_membership_bookings = create_membership_bookings(yoga_class_booking, user, session_amount, billing_number,
                                                             db)
        membership_bookings_id = mew_membership_bookings.id

        # Create new yoga booking

        new_yoga_class_booking = create_new_yoga_class_booking(yoga_class_booking, user, formatted_session_date,
                                                               membership_bookings_id, db)
        # Create new yoga booking if more sessions are added

        if more_session_array:
            for sessions_date in yoga_class_booking.booking_more_sessions:
                updated_date = formatted_date(sessions_date)
                yoga_class_booking = YogaClassBooking(
                    user_id=user.id,
                    session_ref=random_string_ref(),
                    yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
                    yoga_session_name=yoga_class_booking.yoga_session_name,
                    yoga_session_id=yoga_class_booking.yoga_session_id,
                    booking_date=updated_date,
                    booking_slot_time=yoga_class_booking.booking_slot_time,
                    # booking_slot_number=yoga_class_booking.booking_slot_number,
                    transaction_id=membership_bookings_id,
                    booking_status="Pending",
                    payment_status="Pending",
                    mode_of_payment="Momo/Card",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(yoga_class_booking)
                db.commit()
        # Initialize the payment request to DPO
        make_payment = DPO_payment_request(billing_country, session_amount, first_name, last_name, receiver_address,
                                           receiver_city, receiver_email, billing_number, db, mew_membership_bookings)
        return make_payment


@router.post("/createUsingCredits")
async def create_yoga_class_booking_using_credits(yoga_class_booking: YogaClassBookingCreate, db: db_dependency):
    receiver_name = yoga_class_booking.billing_names
    name_parts = receiver_name.split()
    # Extract the first and last names
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])
    receiver_email = yoga_class_booking.billing_email
    receiver_address = yoga_class_booking.billing_address
    receiver_city = yoga_class_booking.billing_city
    receiver_address = yoga_class_booking.billing_address
    formatted_session_date = formatted_date(yoga_class_booking.booking_date)
    billing_number = yoga_class_booking.billing_phone_number
    billing_country = yoga_class_booking.billing_country_id
    session_class_name = yoga_class_booking.yoga_session_name

    more_session_array = yoga_class_booking.booking_more_sessions
    length_of_session = len(more_session_array)
    session_package_info = db.query(models.YogaSessions).filter(
        models.YogaSessions.id == yoga_class_booking.yoga_session_id).first()
    session_amount = session_package_info.price

    if session_package_info.name == "DROP IN":
        new_amount = int(session_amount) * (length_of_session + 1)
        session_amount = new_amount

    user = db.query(User).filter(User.email == yoga_class_booking.billing_email).first()
    # Deduct credits
    deduct_session_credits(user, session_class_name, session_package_info, more_session_array, db)
    # Create new membership booking
    membership_bookings = MembershipBookings(
        user_id=user.id,
        yoga_session_id=yoga_class_booking.yoga_session_id,
        billing_country_id=yoga_class_booking.billing_country_id,
        billing_names=yoga_class_booking.billing_names,
        billing_email=yoga_class_booking.billing_email,
        billing_phone_number=billing_number,
        billing_address=yoga_class_booking.billing_address,
        billing_city=yoga_class_booking.billing_city,
        transaction_amount="0",
        payment_status="Paid",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(membership_bookings)
    db.commit()
    membership_bookings_id = membership_bookings.id
    # Create new yoga booking

    yoga_class_booking = YogaClassBooking(
        user_id=user.id,
        session_ref=yoga_class_booking.session_ref,
        yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
        yoga_session_name=yoga_class_booking.yoga_session_name,
        yoga_session_id=yoga_class_booking.yoga_session_id,
        booking_date=formatted_session_date,
        booking_slot_time=yoga_class_booking.booking_slot_time,
        # booking_slot_number=yoga_class_booking.booking_slot_number,
        transaction_id=membership_bookings_id,
        booking_status="Approved",
        payment_status="Paid",
        mode_of_payment="Credits",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(yoga_class_booking)
    db.commit()

    if more_session_array:
        for sessions_date in more_session_array:
            updated_date = formatted_date(sessions_date)
            yoga_class_booking = YogaClassBooking(
                user_id=user.id,
                session_ref=random_string_ref(),
                yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
                yoga_session_name=yoga_class_booking.yoga_session_name,
                yoga_session_id=yoga_class_booking.yoga_session_id,
                booking_date=updated_date,
                booking_slot_time=yoga_class_booking.booking_slot_time,
                # booking_slot_number=yoga_class_booking.booking_slot_number,
                transaction_id=membership_bookings_id,
                booking_status="Approved",
                payment_status="Paid",
                mode_of_payment="Credits",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(yoga_class_booking)
            db.commit()

    # Initialize confirmation email
    booking_session_info = yoga_class_booking
    send_email = send_confirmation_email(booking_session_info, membership_bookings, db)
    return send_email


@router.get("/check_user_credits")
async def check_user_credits(user_id: int, session_class_name: str, db: db_dependency):
    check_user_credits = db.query(SessionCredits).filter(SessionCredits.user_id == user_id).filter(
        SessionCredits.session_class_name == session_class_name).first()
    if check_user_credits:
        return {"remaining_credits": check_user_credits.remaining_credits}
    else:
        return {"remaining_credits": 0}
@router.post("/update_payment")
async def update_payment_status(transId: str, pnrID: str, ccdApproval: str, transactionToken: str, companyRef: str,
                                db: db_dependency):
    # Check if transaction exists
    check_transaction = db.query(MembershipBookings).filter(MembershipBookings.transaction_token == transId).first()
    # Check Yoga Class Booking
    session_yoga_info = db.query(YogaClassBooking).filter(
        YogaClassBooking.transaction_id == check_transaction.id).count()
    # remaining_balance = check_transaction.transaction_amount - (15000 * session_yoga_info)
    if check_transaction.payment_status == "Pending":
        check_transaction.PnrID = pnrID
        check_transaction.CCDapproval = ccdApproval
        check_transaction.transaction_id = transactionToken
        check_transaction.payment_status = "Paid"
        # check_transaction.remaing_balance = remaining_balance
        db.commit()
        yoga_class_booking = db.query(YogaClassBooking).filter(
            YogaClassBooking.transaction_id == check_transaction.id).all()
        for booking in yoga_class_booking:
            booking.payment_status = "Paid"
            booking.booking_status = "Approved"
            db.commit()
        booking_session_info = db.query(YogaClassBooking).filter(
            YogaClassBooking.transaction_id == check_transaction.id).first()

        # Send confirmation email
        send_email = send_confirmation_email(booking_session_info, check_transaction, db)
        return send_email


@router.get("/spot_available")
async def get_spot_available(yoga_session_name: str, booking_date: str, db: db_dependency):
    formatted_session_date = formatted_date(booking_date)

    yoga_class_booking = db.query(YogaClassBooking).filter(
        YogaClassBooking.yoga_session_name == yoga_session_name,
        YogaClassBooking.booking_date == formatted_session_date,
        YogaClassBooking.payment_status == "paid"
    ).count()
    if yoga_class_booking < 10:
        return {10 - yoga_class_booking}
    else:
        return {0}


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


@router.post("/makePayment")
async def makePayment(PaymentDetails: PaymentDetails):
    randomStringRef = random_string_ref()
    return randomStringRef
    amount = PaymentDetails.amount
    currency = "RWF"
    company_ref = "0"
    redirect_url = "https://www.google.rw/"
    back_url = "https://www.google.rw/"
    service_description = PaymentDetails.serviceDescription
    service_date = datetime.now().strftime('%Y/%m/%d %H:%M')
    customerFirstName = "Elysee"
    customerLastName = "Confiance"
    customerAddress = "KK 237st"
    customerCity = "Kigali"
    customerCountry = "RW"
    customerPhone = "0782384772"
    customerEmail = "ccelyse1@gmail.com"
    DefaultPayment = "MO"
    CompanyAccRef = "gl1qtdego0q"
    url = os.getenv("DPO_ENDPOINT")
    dpo_company_token = os.getenv("DPO_COMPANY_TOKEN")
    services_code = os.getenv("DPO_SERVICE_CODE")
    # xml = '<?xml version="1.0" encoding="utf-8"?><API3G><CompanyToken>57466282-EBD7-4ED5-B699-8659330A6996</CompanyToken><Request>createToken</Request><Transaction><PaymentAmount>450.00</PaymentAmount><PaymentCurrency>USD</PaymentCurrency><CompanyRef>49FKEOA</CompanyRef><RedirectURL>http://www.domain.com/payurl.php</RedirectURL><BackURL>http://www.domain.com/backurl.php </BackURL><CompanyRefUnique>0</CompanyRefUnique><PTL>5</PTL></Transaction><Services><Service><ServiceType>45</ServiceType><ServiceDescription>Flight from Nairobi to Diani</ServiceDescription><ServiceDate>2013/12/20 19:00</ServiceDate></Service></Services></API3G>'
    xml = f'''<?xml version="1.0" encoding="utf-8"?>
                  <API3G>
                    <CompanyToken>{dpo_company_token}</CompanyToken>
                    <Request>createToken</Request>
                    <Transaction>
                      <PaymentAmount>{amount}</PaymentAmount>
                      <PaymentCurrency>{currency}</PaymentCurrency>
                      <CompanyRef>{company_ref}</CompanyRef>
                      <RedirectURL>{redirect_url}</RedirectURL>
                      <BackURL>{back_url}</BackURL>
                      <CompanyRefUnique>{company_ref}</CompanyRefUnique>
                      <customerFirstName>{customerFirstName}</customerFirstName>
                      <customerLastName>{customerLastName}</customerLastName>
                      <customerAddress>{customerAddress}</customerAddress>
                      <customerCity>{customerCity}</customerCity>
                      <customerCountry>{customerCountry}</customerCountry>
                      <customerPhone>{customerPhone}</customerPhone>
                      <customerEmail>{customerEmail}</customerEmail>
                      <DefaultPayment>{DefaultPayment}</DefaultPayment>
                      <CompanyAccRef>{CompanyAccRef}</CompanyAccRef>
                      <PTL>5</PTL>
                    </Transaction>
                    <Services>
                      <Service>
                        <ServiceType>{services_code}</ServiceType>
                        <ServiceDescription>{service_description}</ServiceDescription>
                        <ServiceDate>{service_date}</ServiceDate>
                      </Service>
                    </Services>
                  </API3G>'''
    headers = {'Content-Type': 'application/xml'}
    # r = requests.post(url, data=xml, headers=headers)
    try:
        response = requests.post(url, data=xml, headers=headers)
        response.raise_for_status()  # Raise an exception for bad responses (4xx, 5xx)
        xml_response = response.text
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        # Parse XML
        root = ET.fromstring(xml_response)
        # Convert XML to dictionary
        result_data = {}
        for child in root:
            result_data[child.tag] = child.text

        if result_data['Result'] == "000":
            trans_token = result_data['TransToken']
            trans_ref = result_data['TransRef']
            trans_message = result_data['ResultExplanation']
            return result_data
        else:
            return result_data['ResultExplanation']
    except requests.exceptions.RequestException as e:
        # Handle request exceptions (connection errors, timeouts, etc.)
        return {"error": str(e)}


@router.get('/send_test_mail')
async def send_test_mail():
    subject = f"Thank you for Booking a session at SafeSpace Studio!"
    # message = f"Your scheduled yoga session with is confirmed for {booking_session_info.booking_date} at {booking_session_info.booking_slot_time}. You will receive an email if anything changes."
    smtp_server = os.getenv("MAILGUN_SMTP_SERVER")
    smtp_port = int(os.getenv("MAILGUN_SMTP_PORT"))
    smtp_username = os.getenv("MAILGUN_SMTP_USERNAME")
    smtp_password = os.getenv("MAILGUN_SMTP_PASSWORD")

    # Read the email template
    email_template_content = read_email_custom_template_booking()

    # Create a Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader(os.path.join(os.getcwd(), "templates", "email")))
    template = env.from_string(email_template_content)

    # Render the template with the provided data
    email_content = template.render()

    # Create the email content
    email = EmailMessage()
    email["From"] = f"SafeSpaceYoga.rw <{smtp_username}>"
    email["To"] = "ccelyse1@gmail.com"
    email["Subject"] = subject
    email.set_content("This is the plain text content.")
    email.add_alternative(email_content, subtype="html")
    # Attach the image
    image_path = "templates/email/logo.png"
    with open(image_path, "rb") as img_file:
        image = MIMEImage(img_file.read())
        image.add_header("Content-ID", "logo.png")
        email.attach(image)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(email)

    return {"message": "Email sent successfully"}
