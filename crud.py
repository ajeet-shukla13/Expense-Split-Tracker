from sqlalchemy.orm import Session
from . import models, schemas
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
from sqlalchemy import func
import heapq

def create_user(db: Session, name: str, email: str = None):
    u = models.User(name=name, email=email)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def create_group(db: Session, name: str):
    g = models.Group(name=name)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g

def add_member(db: Session, group_id: int, user_id: int):
    gm = models.GroupMember(group_id=group_id, user_id=user_id)
    db.add(gm)
    db.commit()
    db.refresh(gm)
    return gm

def get_group_members(db: Session, group_id: int):
    rows = db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()
    return [r.user_id for r in rows]

def add_expense(db: Session, group_id: int, expense_in: schemas.ExpenseCreate):
    # ------------------ NEW VALIDATION ---------------------
    # Check group exists
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise ValueError("Group does not exist")

    # Expense amount must be positive
    if Decimal(expense_in.amount) <= 0:
        raise ValueError("Expense amount must be positive")

    # Validate users in paid_by
    for p in expense_in.paid_by:
        if Decimal(p.amount) < 0:
            raise ValueError("Negative payment not allowed")
        user = db.query(models.User).filter(models.User.id == p.user_id).first()
        if not user:
            raise ValueError(f"User {p.user_id} does not exist")

    # Validate splits
    if expense_in.splits:
        for s in expense_in.splits:
            if Decimal(s.amount) < 0:
                raise ValueError("Negative split not allowed")
            user = db.query(models.User).filter(models.User.id == s.user_id).first()
            if not user:
                raise ValueError(f"User {s.user_id} does not exist")

    # Validate users for equal split
    if expense_in.users:
        for uid in expense_in.users:
            user = db.query(models.User).filter(models.User.id == uid).first()
            if not user:
                raise ValueError(f"User {uid} does not exist")
                
    # Percentages check
    if expense_in.percentages:
        for uid, pct in expense_in.percentages.items():
            if Decimal(pct) < 0:
                raise ValueError("Negative percentage not allowed")
            user = db.query(models.User).filter(models.User.id == int(uid)).first()
            if not user:
                raise ValueError(f"User {uid} does not exist")

    # ------------------ CORE SPLIT LOGIC --------------------
    total_paid = sum([p.amount for p in expense_in.paid_by])
    if Decimal(total_paid) != Decimal(expense_in.amount):
        raise ValueError("Sum of paid_by amounts must equal total amount")

    shares: Dict[int, Decimal] = {}
    amt = Decimal(expense_in.amount)

    if expense_in.split_type == "equal":
        users = expense_in.users
        if not users:
            raise ValueError("Provide users for equal split")
        n = len(users)
        base = (amt / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        shares = {uid: base for uid in users}
        pennies = int((amt * 100) - int(base * 100) * n)
        for i in range(pennies):
            uid = users[i % n]
            shares[uid] += Decimal("0.01")

    elif expense_in.split_type == "exact":
        if not expense_in.splits:
            raise ValueError("Exact split requires splits list")
        ssum = sum([s.amount for s in expense_in.splits])
        if Decimal(ssum) != amt:
            raise ValueError("Sum of exact splits must equal total amount")
        for s in expense_in.splits:
            shares[s.user_id] = Decimal(s.amount)

    elif expense_in.split_type == "percentage":
        if not expense_in.percentages:
            raise ValueError("percentages required")
        total_pct = sum([Decimal(v) for v in expense_in.percentages.values()])
        if total_pct != Decimal("100"):
            raise ValueError("Percentages must sum to 100")
        for uid, pct in expense_in.percentages.items():
            shares[int(uid)] = (amt * Decimal(pct) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        raise ValueError("Unknown split_type")

    expense = models.Expense(
        group_id=group_id,
        description=expense_in.description,
        amount=amt,
        currency=expense_in.currency
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    for p in expense_in.paid_by:
        db.add(models.ExpensePayer(expense_id=expense.id, user_id=p.user_id, amount=Decimal(p.amount)))

    for uid, a in shares.items():
        db.add(models.ExpenseShare(expense_id=expense.id, user_id=uid, amount=a))

    db.commit()
    return expense

def compute_group_balances(db: Session, group_id: int):
    members = db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()
    user_ids = [m.user_id for m in members]
    balances = {}
    for uid in user_ids:
        paid = db.query(func.coalesce(func.sum(models.ExpensePayer.amount), 0)).join(
            models.Expense, models.Expense.id == models.ExpensePayer.expense_id
        ).filter(models.Expense.group_id == group_id, models.ExpensePayer.user_id == uid).scalar() or 0

        share = db.query(func.coalesce(func.sum(models.ExpenseShare.amount), 0)).join(
            models.Expense, models.Expense.id == models.ExpenseShare.expense_id
        ).filter(models.Expense.group_id == group_id, models.ExpenseShare.user_id == uid).scalar() or 0

        received = db.query(func.coalesce(func.sum(models.Settlement.amount), 0)).filter(
            models.Settlement.group_id == group_id, models.Settlement.payee_id == uid
        ).scalar() or 0

        paid_sett = db.query(func.coalesce(func.sum(models.Settlement.amount), 0)).filter(
            models.Settlement.group_id == group_id, models.Settlement.payer_id == uid
        ).scalar() or 0

        net = Decimal(paid) - Decimal(share) + Decimal(paid_sett) - Decimal(received)
        balances[uid] = net.quantize(Decimal("0.01"))
    return balances

def add_settlement(db: Session, group_id: int, payer_id: int, payee_id: int, amount):
    # Validate group exists
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise ValueError("Group does not exist")
    
    # Validate user exists
    payer = db.query(models.User).filter(models.User.id == payer_id).first()
    payee = db.query(models.User).filter(models.User.id == payee_id).first()
    if not payer or not payee:
        raise ValueError("Payer or payee does not exist")

    balances = compute_group_balances(db, group_id)
    payer_net = balances.get(payer_id, Decimal('0'))
    payee_net = balances.get(payee_id, Decimal('0'))

    if payer_net >= 0:
        raise ValueError("Payer does not owe anything")
    if payee_net <= 0:
        raise ValueError("Payee not owed anything")

    amount = Decimal(amount)
    if amount > min(abs(payer_net), payee_net):
        raise ValueError("Cannot settle more than outstanding")

    s = models.Settlement(group_id=group_id, payer_id=payer_id, payee_id=payee_id, amount=amount)
    db.add(s)
    db.commit()
    return compute_group_balances(db, group_id)

def simplify_debts(db: Session, group_id: int):
    balances = compute_group_balances(db, group_id)

    # Build min-heap for debtors and max-heap for creditors (negated for heapq)
    debtors = []
    creditors = []
    for uid, amt in balances.items():
        if amt < 0:
            heapq.heappush(debtors, (amt, uid))        # amt negative
        elif amt > 0:
            heapq.heappush(creditors, (-amt, uid))     # amt positive, negate for max-heap

    while debtors and creditors:
        debt_amt, debtor_uid = heapq.heappop(debtors)
        credit_amt, creditor_uid = heapq.heappop(creditors)
        settle_amt = min(-debt_amt, -credit_amt)

        # Record settlement in DB
        db.add(models.Settlement(
            group_id=group_id, payer_id=debtor_uid, payee_id=creditor_uid, amount=settle_amt
        ))

        new_debt = debt_amt + settle_amt
        new_credit = credit_amt + settle_amt
        if new_debt < 0:
            heapq.heappush(debtors, (new_debt, debtor_uid))
        if new_credit < 0:
            heapq.heappush(creditors, (new_credit, creditor_uid))

    db.commit()
    return compute_group_balances(db, group_id)
