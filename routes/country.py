from typing import Annotated, List
from fastapi import APIRouter, HTTPException, Depends
from database import db_dependency
from starlette import status

import models
import schemas

router = APIRouter(
    tags=["Country"],
    prefix='/country'
)


@router.get("/list")
async def get_countries(db: db_dependency):
    country_list = db.query(models.Country).all()
    return country_list


@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_country(db: db_dependency, country_request: schemas.CountryBase):
    country = db.query(models.Country).filter(models.Country.name == country_request.name).first()
    if country is None:
        try:
            # add_country = models.Country(
            #     name=country_request.name,
            #     code=country_request.code
            # )
            add_country = models.Country(**country_request.model_dump())
            db.add(add_country)
            db.commit()
            db.refresh(add_country)
            return {'message': "Successfully added new country", "result": add_country}
        except Exception as e:
            db.rollback()  # Roll back the transaction in case of an exception
            return {'message': "Error adding country"}
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Country already exists in the database")


@router.post("/update/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.CountryOut)
async def update_country(db: db_dependency, country_request: schemas.CountryUpdate, country_id: int):
    find_country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if find_country is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Country not found")
    for key, value in country_request.model_dump().items():
        setattr(find_country, key, value)
    db.commit()
    db.refresh(find_country)
    return {'message': "Successfully updated country", "result": find_country}


@router.post("/delete/{id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_country(db: db_dependency, country_id: int):
    delete_country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if delete_country is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Country not found")
    db.delete(delete_country)
    db.commit()
    return {'message': "Successfully deleted country"}
