from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud
from ..database import get_db

router = APIRouter(tags=["Settlements"])

@router.post("/groups/{group_id}/settle", summary="Settle a debt")
def settle(group_id: int, body: dict, db: Session = Depends(get_db)):
    try:
        return crud.add_settlement(db, group_id, body['payer_id'], body['payee_id'], body['amount'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/groups/{group_id}/simplify", summary="Simplify debts")
def simplify(group_id: int, db: Session = Depends(get_db)):
    return crud.simplify_debts(db, group_id)
