from datetime import datetime, timedelta

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
                'name': 'Hatha - Safe Space',
                'time': '06:30 PM',
                'location': 'Yoga Studio - Kiyovu, KN 52 NUMBER 28'
            }]
        elif current_day.weekday() == 1:  # Check if it's Wednesday (0 for Monday, 1 for Tuesday, and so on)
            day_info['sessions'] = [
                {
                    'name': 'Hatha - Safe Space',
                    'time': '07:00 AM',
                    'location': 'Safe Space Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                },
                {
                    'name': 'Hatha - Kigali Wellness Hub',
                    'time': '12:30 PM',
                    'location': 'Kigali Wellness Hub- Kacyiru, Mercy house 97 KG 5 AVE'
                }]
        elif current_day.weekday() == 2:
            day_info['sessions'] = [
                {
                    'name': 'Hatha - Safe Space',
                    'time': '05:30 PM',
                    'location': 'Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                }]
        elif current_day.weekday() == 3:
            day_info['sessions'] = [
                {
                    'name': 'Hatha - Safe Space',
                    'time': '05:30 PM',
                    'location': 'Safe Space Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                },
                {
                    'name': 'Hatha Flow- Safe Space',
                    'time': '07:00 PM',
                    'location': 'Safe Space Yoga Studio - Kiyovu, KN 52 NUMBER 28'
                }]
        elif current_day.weekday() == 4:
            day_info['sessions'] = [
                {
                    'name': 'Hatha - Kigali Wellness Hub',
                    'time': '04:30 PM',
                    'location': 'Kigali Wellness Hub- Kacyiru, Mercy house 97 KG 5 AVE'
                }]
        elif current_day.weekday() == 5:
            day_info['sessions'] = [
                {
                    'name': 'Hatha - Kigali Wellness Hub',
                    'time': '09:00 - 11 AM',
                    'location': 'Kigali Wellness Hub- Kacyiru, Mercy house 97 KG 5 AVE'
                }]
        if current_day.weekday() == 6:  # Sunday (0 for Monday, 1 for Tuesday, and so on)
            continue

        list_day.append(day_info)
    return list_day
    # if datetime.now().weekday() == 1:  # Check if today is Monday (0 for Monday, 1 for Tuesday, and so on)
    #     monday_info = {
    #         "days": "Tuesday January 09",
    #         "sessions": {
    #             'name': 'Your Name',
    #             'time': '10:00 AM',
    #             'location': 'Your Location'
    #         }
    #     }
    #     list_days.append(monday_info)
    # return list_days

    # return {"list_days": list_days}
