from pydantic import BaseModel, condecimal
from decimal import Decimal
from typing import Optional, List, Dict

Money = condecimal(max_digits=12, decimal_places=2)

class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None   # Default None so missing email works

class GroupCreate(BaseModel):
    name: str

class AddMember(BaseModel):
    user_id: int

class ExpensePayerSchema(BaseModel):
    user_id: int
    amount: Money

class ExpenseShareSchema(BaseModel):
    user_id: int
    amount: Money

class ExpenseCreate(BaseModel):
    description: Optional[str] = None
    amount: Money
    currency: Optional[str] = "USD"
    paid_by: List[ExpensePayerSchema]
    split_type: str
    splits: Optional[List[ExpenseShareSchema]] = None
    percentages: Optional[Dict[int, condecimal(max_digits=5, decimal_places=2)]] = None
    users: Optional[List[int]] = None


class SettlementCreate(BaseModel):
    payer_id: int
    payee_id: int
    amount: Money