# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Enum
from sqlalchemy.orm import relationship
from .database import Base
from decimal import Decimal
import enum
import datetime

class SplitType(str, enum.Enum):
    equal = "equal"
    exact = "exact"
    percentage = "percentage"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    description = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExpensePayer(Base):
    __tablename__ = "expense_payers"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Numeric(12, 2), nullable=False)

class ExpenseShare(Base):
    __tablename__ = "expense_shares"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Numeric(12, 2), nullable=False)

class Settlement(Base):
    __tablename__ = "settlements"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    payer_id = Column(Integer, ForeignKey("users.id"))
    payee_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Numeric(12,2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
