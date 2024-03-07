from datetime import datetime, timedelta, date
import calendar
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import db_dependency
from starlette import status
from typing import List, Optional, Annotated
from models import YogaClassBooking

router = APIRouter(
    tags=["Planning"],
    prefix='/planning'
)


def formatted_date(date_input):
    current_year = datetime.now().year
    input_date = datetime.strptime(date_input + f" {current_year}", "%A %B %d %Y")

    # Format the date in the desired format
    formatted_date = input_date.strftime("%Y-%m-%d 00:00:00")

    return formatted_date


@router.get("/list")
async def list_planning(db: db_dependency):
    # list day of the current week and the next week
    list_days = [(datetime.now() + timedelta(days=i)).strftime('%A %B %d') for i in range(7)]
    list_day = []
    for i in range(7):  # Start from Tuesday (index 1) as Monday info is already added
        current_day = datetime.now() + timedelta(days=i)
        day_info = {
            'days': (datetime.now() + timedelta(days=i)).strftime('%A %B %d')
        }
        if current_day.weekday() == 0:  # Check if it's Tuesday (0 for Monday, 1 for Tuesday, and so on)
            day_info['sessions'] = [{
                'id': 1,
                'name': 'Hatha - Safe Space',
                'time': '06:30 PM',
                'location': 'Yoga Studio - Kiyovu, KN 52 NUMBER 28'
            }]
        elif current_day.weekday() == 1:  # Check if it's Wednesday (0 for Monday, 1 for Tuesday, and so on)
            day_info['sessions'] = [
                {
                    'id': 2,
                    'name': 'Hatha - Safe Space',
                    'time': '07:00 AM',
                    'location': 'Safe Space Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                }]
        elif current_day.weekday() == 2:
            day_info['sessions'] = [
                {
                    'id': 3,
                    'name': 'Hatha - Safe Space',
                    'time': '05:30 PM',
                    'location': 'Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                }]
        elif current_day.weekday() == 3:
            day_info['sessions'] = [
                {
                    'id': 4,
                    'name': 'Hatha - Safe Space',
                    'time': '05:30 PM',
                    'location': 'Safe Space Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                },
                {
                    'id': 5,
                    'name': 'Hatha Flow- Safe Space',
                    'time': '07:00 PM',
                    'location': 'Safe Space Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                }]
        elif current_day.weekday() == 4:
            day_info['sessions'] = [
                {
                    'id': 6,
                    'name': 'Sadhana - Kigali Wellness Hub',
                    'time': '05:30  - 7 PM',
                    'location': 'Kigali Wellness Hub- Kacyiru, Mercy house 97 KG 5 AVE'
                }]
        elif current_day.weekday() == 5:
            continue
        if current_day.weekday() == 6:
            continue
        list_day.append(day_info)
    return list_day


@router.get("/session_weekly_list")
async def session_weekly_list(
    today_date: str,
    yoga_session_name: str,
    db: db_dependency
):
    # Parse the input date string and set the year to the current year
    current_date = datetime.now()
    input_date = datetime.strptime(today_date, "%A %B %d").replace(year=current_date.year)

    # Get the day of the week of the provided date
    provided_weekday = input_date.weekday()

    # Calculate the first occurrence of the provided day in the current month
    first_day_of_current_month = current_date.replace(day=1)
    first_occurrence_of_day = first_day_of_current_month + timedelta(
        days=(provided_weekday - first_day_of_current_month.weekday() + 7) % 7)

    # Calculate the last day of the current month
    last_day_of_current_month = (first_day_of_current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Generate a list of all occurrences of the provided day in the current month
    occurrences_of_day = [first_occurrence_of_day + timedelta(weeks=i * 1) for i in
                          range((last_day_of_current_month - first_occurrence_of_day).days // 7 + 1)]

    # Format the dates
    formatted_dates = [date.strftime('%A %B %d') for date in occurrences_of_day]
    weekly_plan = []
    for date in formatted_dates:
        check_available_spots = db.query(YogaClassBooking).filter(
            YogaClassBooking.yoga_session_name == yoga_session_name,
            YogaClassBooking.booking_date == formatted_date(date),
            YogaClassBooking.payment_status == "paid"
        ).count()
        if check_available_spots < 10:
            available_spots = 10 - check_available_spots
        else:
            available_spots = 0

        weekly_plan.append({
            'date': date,
            'available_spots': available_spots
        })
    return weekly_plan
    # # Find the index of the first Monday in the current month
    # first_day_of_month = day_date.replace(day=1)
    # first_monday = first_day_of_month + timedelta(days=(calendar.MONDAY - first_day_of_month.weekday() + 7) % 7)
    #
    # # List all remaining Mondays in the current month
    # remaining_mondays_current_month = [first_monday + timedelta(weeks=i) for i in
    #                                    range((31 - first_monday.day) // 7 + 1) if
    #                                    (first_monday + timedelta(weeks=i)).month == current_month and (
    #                                            first_monday + timedelta(weeks=i)) > day_date]
    #
    # # List all Mondays in the next month
    # next_month = current_month + 1 if current_month < 12 else 1
    # next_year = current_year + 1 if current_month == 12 else current_year
    # first_day_of_next_month = day_date.replace(month=next_month, year=next_year, day=1)
    # first_monday_next_month = first_day_of_next_month + timedelta(
    #     days=(calendar.MONDAY - first_day_of_next_month.weekday() + 7) % 7)
    # all_mondays_next_month = [first_monday_next_month + timedelta(weeks=i) for i in range(4)]
    # days = remaining_mondays_current_month + all_mondays_next_month
    # formatted_mondays = [date.strftime('%A %B %d') for date in days]
    # weekly_plan = []
    # for date in formatted_mondays:
    #     check_available_spots = db.query(YogaClassBooking).filter(
    #         YogaClassBooking.yoga_session_name == yoga_session_name,
    #         YogaClassBooking.booking_date == formatted_date(date),
    #         YogaClassBooking.payment_status == "paid"
    #     ).count()
    #     if check_available_spots < 10:
    #         available_spots = 10 - check_available_spots
    #     else:
    #         available_spots = 0
    #
    #     weekly_plan.append({
    #         'date': date,
    #         'available_spots': available_spots
    #     })
    # return weekly_plan

