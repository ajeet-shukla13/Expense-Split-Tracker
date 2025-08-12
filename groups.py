from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from decimal import Decimal

router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)

@router.post("", summary="Create a group")
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    return crud.create_group(db, group.name)

@router.post("/{group_id}/members", summary="Add member to group")
def add_member(group_id: int, member: schemas.AddMember, db: Session = Depends(get_db)):
    return crud.add_member(db, group_id, member.user_id)

@router.post("/{group_id}/expenses", summary="Add expense to group")
def add_expense(group_id: int, expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    try:
        return crud.add_expense(db, group_id, expense)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{group_id}/expenses/balances", summary="Get group balances")
def get_balances(group_id: int, db: Session = Depends(get_db)):
    """
    Returns balances in list of dicts format: [{"user_id": ..., "net": ...}]
    """
    try:
        balances = crud.compute_group_balances(db, group_id)
        # Convert Decimal to float for JSON + make list of dicts
        return [{"user_id": uid, "net": float(net)} for uid, net in balances.items()]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{group_id}/settle", summary="Settle a debt between two users")
def settle_debt(group_id: int, settlement: schemas.SettlementCreate, db: Session = Depends(get_db)):
    try:
        return crud.add_settlement(
            db,
            group_id=group_id,
            payer_id=settlement.payer_id,
            payee_id=settlement.payee_id,
            amount=Decimal(settlement.amount)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{group_id}/simplify", summary="Simplify debts in a group")
def simplify(group_id: int, db: Session = Depends(get_db)):
    try:
        return crud.simplify_debts(db, group_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
