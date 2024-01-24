import os
import smtplib
from datetime import datetime
from email.mime.image import MIMEImage

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import db_dependency
from starlette import status
from models import YogaClassBooking, User, MembershipBookings, YogaSessions, Country
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
    receiver_email = yoga_class_booking.billing_email
    receiver_address = yoga_class_booking.billing_address
    receiver_city = yoga_class_booking.billing_city
    receiver_address = yoga_class_booking.billing_address
    formatted_session_date = formatted_date(yoga_class_booking.booking_date)
    billing_number = yoga_class_booking.billing_phone_number
    contry_code = db.query(models.Country).filter(models.Country.id == yoga_class_booking.billing_country_id).first()

    more_session_array = yoga_class_booking.booking_more_sessions
    if yoga_class_booking.password == "":
        user = db.query(User).filter(User.email == yoga_class_booking.billing_email).first()
        membership_bookings = MembershipBookings(
            user_id=user.id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            billing_country_id=yoga_class_booking.billing_country_id,
            billing_names=yoga_class_booking.billing_names,
            billing_email=yoga_class_booking.billing_email,
            billing_phone_number=billing_number,
            billing_address=yoga_class_booking.billing_address,
            billing_city=yoga_class_booking.billing_city,
            payment_status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(membership_bookings)
        db.commit()
        yoga_class_booking = YogaClassBooking(
            user_id=user.id,
            yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
            yoga_session_id=yoga_class_booking.yoga_session_id,
            booking_date=formatted_session_date,
            booking_slot_time=yoga_class_booking.booking_slot_time,
            # booking_slot_number=yoga_class_booking.booking_slot_number,
            transaction_id=membership_bookings.id,
            booking_status="Pending",
            payment_status="Pending",
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
                    yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
                    yoga_session_id=yoga_class_booking.yoga_session_id,
                    booking_date=updated_date,
                    booking_slot_time=yoga_class_booking.booking_slot_time,
                    # booking_slot_number=yoga_class_booking.booking_slot_number,
                    transaction_id=membership_bookings.id,
                    booking_status="Pending",
                    payment_status="Pending",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(yoga_class_booking)
                db.commit()
        amount = "10"
        currency = "RWF"
        company_ref = "0"
        redirect_url = "https://www.google.rw/"
        back_url = "https://www.google.rw/"
        service_description = "Yoga class session booking"
        service_date = datetime.now().strftime('%Y/%m/%d %H:%M')
        customerCountry = contry_code.code
        DefaultPayment = "MO"

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
                           <customerFirstName>{receiver_name}</customerFirstName>
                           <customerAddress>{receiver_address}</customerAddress>
                           <customerCity>{receiver_city}</customerCity>
                           <customerCountry>{customerCountry}</customerCountry>
                           <customerPhone>{billing_number}</customerPhone>
                           <customerEmail>{receiver_email}</customerEmail>
                           <DefaultPayment>{DefaultPayment}</DefaultPayment>
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
                db.commit()
                return {"message": "Transaction created", "status_code": result_data['Result'],
                        "redirection_url": redirection_url}
            else:
                return {"message": result_data['ResultExplanation'], "status_code": result_data['Result']}
        except requests.exceptions.RequestException as e:
            # Handle request exceptions (connection errors, timeouts, etc.)
            return {"error": str(e)}
        # return {"message": "Yoga Class Booking created successfully"}

    else:
        hashed_password = get_hashed_password(yoga_class_booking.password)
        user = User(
            name=yoga_class_booking.billing_names,
            email=yoga_class_booking.billing_email,
            phone_number=billing_number,
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
            billing_phone_number=billing_number,
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
            booking_date=formatted_session_date,
            booking_slot_time=yoga_class_booking.booking_slot_time,
            # booking_slot_number=yoga_class_booking.booking_slot_number,
            transaction_id=membership_bookings.id,
            booking_status="Pending",
            payment_status="Pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(yoga_class_booking)
        db.commit()
        db.refresh(membership_bookings)

        if more_session_array:
            for sessions_date in yoga_class_booking.booking_more_sessions:
                updated_date = formatted_date(sessions_date)
                yoga_class_booking = YogaClassBooking(
                    user_id=user.id,
                    yoga_class_location_id=yoga_class_booking.yoga_class_location_id,
                    yoga_session_id=yoga_class_booking.yoga_session_id,
                    booking_date=updated_date,
                    booking_slot_time=yoga_class_booking.booking_slot_time,
                    # booking_slot_number=yoga_class_booking.booking_slot_number,
                    transaction_id=membership_bookings.id,
                    booking_status="Pending",
                    payment_status="Pending",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(yoga_class_booking)
                db.commit()
        amount = "10"
        currency = "RWF"
        company_ref = "0"
        redirect_url = "https://www.google.rw/"
        back_url = "https://www.google.rw/"
        service_description = "Yoga class session booking"
        service_date = datetime.now().strftime('%Y/%m/%d %H:%M')
        customerCountry = contry_code.code
        DefaultPayment = "MO"

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
                           <customerFirstName>{receiver_name}</customerFirstName>
                           <customerAddress>{receiver_address}</customerAddress>
                           <customerCity>{receiver_city}</customerCity>
                           <customerCountry>{customerCountry}</customerCountry>
                           <customerPhone>{billing_number}</customerPhone>
                           <customerEmail>{receiver_email}</customerEmail>
                           <DefaultPayment>{DefaultPayment}</DefaultPayment>
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
                membership_bookings_transaction = db.query(MembershipBookings).filter(MembershipBookings.id == membership_bookings.id).first()
                membership_bookings_transaction.transaction_token = trans_token
                membership_bookings_transaction.transaction_ref = trans_ref
                db.commit()
                return {"message": "Transaction created", "status_code": result_data['Result'],
                        "redirection_url": redirection_url}
            else:
                return {"message": result_data['ResultExplanation'], "status_code": result_data['Result']}
        except requests.exceptions.RequestException as e:
            # Handle request exceptions (connection errors, timeouts, etc.)
            return {"error": str(e)}

    # subject = f"Thank you for Booking a session at SafeSpace Studio!"
    # message = f"Your scheduled yoga session with is confirmed for {formatted_session_date} at {yoga_class_booking.booking_slot_time}. You will receive an email if anything changes."
    # smtp_server = os.getenv("MAILGUN_SMTP_SERVER")
    # smtp_port = int(os.getenv("MAILGUN_SMTP_PORT"))
    # smtp_username = os.getenv("MAILGUN_SMTP_USERNAME")
    # smtp_password = os.getenv("MAILGUN_SMTP_PASSWORD")
    #
    # # Read the email template
    # email_template_content = read_email_template_booking()
    #
    # # Create a Jinja2 environment and load the template
    # env = Environment(loader=FileSystemLoader(os.path.join(os.getcwd(), "templates", "email")))
    # template = env.from_string(email_template_content)
    #
    # # Render the template with the provided data
    # email_content = template.render(message=message, name=receiver_name)
    #
    # # Create the email content
    # email = EmailMessage()
    # email["From"] = f"SafeSpaceYoga.rw <{smtp_username}>"
    # email["To"] = receiver_email
    # # email["To"] = "ccelyse1@gmail.com"
    # email["Subject"] = subject
    # email.set_content("This is the plain text content.")
    # email.add_alternative(email_content, subtype="html")
    # # Attach the image
    # image_path = "templates/email/logo.png"
    # with open(image_path, "rb") as img_file:
    #     image = MIMEImage(img_file.read())
    #     image.add_header("Content-ID", "logo.png")
    #     email.attach(image)
    #
    # # Connect to the SMTP server and send the email
    # with smtplib.SMTP(smtp_server, smtp_port) as server:
    #     server.starttls()
    #     server.login(smtp_username, smtp_password)
    #     server.send_message(email)

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


@router.post("/makePayment")
async def makePayment(PaymentDetails: PaymentDetails):
    amount  = PaymentDetails.amount
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
    CompanyAccRef = "433nmhjk"
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
