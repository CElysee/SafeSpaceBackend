from datetime import datetime, timedelta, date
import calendar
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import db_dependency
from starlette import status
from typing import List, Optional, Annotated

router = APIRouter(
    tags=["Planning"],
    prefix='/planning'
)


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


@router.get("session_weekly_list")
async def session_weekly_list(db: db_dependency):
    # Parse the input date string
    day_date = datetime.now()
    current_month = day_date.month
    current_year = day_date.year

    # Find the index of the first Monday in the current month
    first_day_of_month = day_date.replace(day=1)
    first_monday = first_day_of_month + timedelta(days=(calendar.MONDAY - first_day_of_month.weekday() + 7) % 7)

    # List all remaining Mondays in the current month
    remaining_mondays_current_month = [first_monday + timedelta(weeks=i) for i in
                                       range((31 - first_monday.day) // 7 + 1) if
                                       (first_monday + timedelta(weeks=i)).month == current_month and (
                                                   first_monday + timedelta(weeks=i)) > day_date]

    # List all Mondays in the next month
    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year + 1 if current_month == 12 else current_year
    first_day_of_next_month = day_date.replace(month=next_month, year=next_year, day=1)
    first_monday_next_month = first_day_of_next_month + timedelta(
        days=(calendar.MONDAY - first_day_of_next_month.weekday() + 7) % 7)
    all_mondays_next_month = [first_monday_next_month + timedelta(weeks=i) for i in range(4)]
    days  = remaining_mondays_current_month + all_mondays_next_month
    formatted_mondays = [date.strftime('%A %B %d') for date in days]

    return formatted_mondays