from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(tags=["Expenses"])

@router.post("/groups/{group_id}/expenses", summary="Add an expense")
def create_expense(group_id: int, expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    try:
        return crud.add_expense(db, group_id, expense)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/groups/{group_id}/expenses/balances", summary="Get balances for group")
def group_balances(group_id: int, db: Session = Depends(get_db)):
    return crud.compute_group_balances(db, group_id)
