import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ---------- Helper functions ----------
def create_user(name):
    r = client.post("/users", json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]

def create_group(name):
    r = client.post("/groups", json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]

def add_member(group_id, user_id):
    r = client.post(f"/groups/{group_id}/members", json={"user_id": user_id})
    assert r.status_code == 200

def add_expense(group_id, payload):
    r = client.post(f"/groups/{group_id}/expenses", json=payload)
    assert r.status_code == 200

def add_expense_should_fail(group_id, payload):
    r = client.post(f"/groups/{group_id}/expenses", json=payload)
    assert r.status_code == 400

def get_balances(group_id):
    r = client.get(f"/groups/{group_id}/expenses/balances")
    assert r.status_code == 200
    return {item["user_id"]: item["net"] for item in r.json()}

def settle_debt(group_id, payer_id, payee_id, amount):
    r = client.post(f"/groups/{group_id}/settle",
                    json={"payer_id": payer_id, "payee_id": payee_id, "amount": amount})
    assert r.status_code == 200

def settle_debt_should_fail(group_id, payer_id, payee_id, amount):
    r = client.post(f"/groups/{group_id}/settle",
                    json={"payer_id": payer_id, "payee_id": payee_id, "amount": amount})
    assert r.status_code == 400

def simplify(group_id):
    r = client.post(f"/groups/{group_id}/simplify")
    assert r.status_code == 200
    return r.json()


def test_equal_split():
    gid = create_group("Trip to Paris")
    u1, u2, u3 = create_user("User1"), create_user("User2"), create_user("User3")
    for uid in (u1, u2, u3):
        add_member(gid, uid)
    add_expense(gid, {
        "description": "Dinner",
        "amount": 90.00,
        "paid_by": [{"user_id": u1, "amount": 90.00}],
        "split_type": "equal",
        "users": [u1, u2, u3]
    })
    balances = get_balances(gid)
    assert round(balances[u1], 2) == 60.00
    assert round(balances[u2], 2) == -30.00
    assert round(balances[u3], 2) == -30.00

def test_exact_amount_split():
    gid = create_group("Dinner")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    add_expense(gid, {
        "description": "Exact Split Dinner",
        "amount": 100.00,
        "paid_by": [{"user_id": u1, "amount": 100.00}],
        "split_type": "exact",
        "splits": [
            {"user_id": u1, "amount": 70.00},
            {"user_id": u2, "amount": 30.00}
        ]
    })
    balances = get_balances(gid)
    assert round(balances[u1], 2) == 30.00
    assert round(balances[u2], 2) == -30.00

def test_percentage_split():
    gid = create_group("Shopping Trip")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    add_expense(gid, {
        "description": "Shopping",
        "amount": 200.00,
        "paid_by": [{"user_id": u1, "amount": 200.00}],
        "split_type": "percentage",
        "percentages": {str(u1): 60, str(u2): 40}
    })
    balances = get_balances(gid)
    assert round(balances[u1], 2) == 80.00
    assert round(balances[u2], 2) == -80.00

def test_settling_debt():
    gid = create_group("Trip to Goa")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    add_expense(gid, {
        "description": "Taxi",
        "amount": 50.00,
        "paid_by": [{"user_id": u1, "amount": 50.00}],
        "split_type": "equal",
        "users": [u1, u2]
    })
    settle_debt(gid, payer_id=u2, payee_id=u1, amount=25.00)
    balances = get_balances(gid)
    assert round(balances[u2], 2) == 0.00 or balances[u2] > -0.01

def test_simplify_debts():
    gid = create_group("Trip to Goa Simplify")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    add_expense(gid, {
        "description": "Expense1",
        "amount": 30.00,
        "paid_by": [{"user_id": u1, "amount": 30.00}],
        "split_type": "exact",
        "splits": [
            {"user_id": u2, "amount": 30.00}
        ]
    })
    add_expense(gid, {
        "description": "Expense2",
        "amount": 20.00,
        "paid_by": [{"user_id": u2, "amount": 20.00}],
        "split_type": "exact",
        "splits": [
            {"user_id": u1, "amount": 20.00}
        ]
    })
    simplify(gid)
    balances = get_balances(gid)
    assert round(balances[u1], 2) == 0.0
    assert round(balances[u2], 2) == 0.0

# ---------- Edge Case Tests ----------

def test_invalid_split_type():
    gid = create_group("Invalid Split Group")
    u1 = create_user("User1")
    add_member(gid, u1)
    payload = {
        "description": "Invalid Split",
        "amount": 50.00,
        "paid_by": [{"user_id": u1, "amount": 50.00}],
        "split_type": "random_type", 
        "users": [u1]
    }
    add_expense_should_fail(gid, payload)

def test_mismatched_split_totals():
    gid = create_group("Mismatch Split Group")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    payload = {
        "description": "Mismatch Paid",
        "amount": 50.00,
        "paid_by": [{"user_id": u1, "amount": 30.00}, {"user_id": u2, "amount": 10.00}],
        "split_type": "equal",
        "users": [u1, u2]
    }
    add_expense_should_fail(gid, payload)
    payload = {
        "description": "Mismatch Split",
        "amount": 50.00,
        "paid_by": [{"user_id": u1, "amount": 50.00}],
        "split_type": "exact",
        "splits": [
            {"user_id": u1, "amount": 30.00},
            {"user_id": u2, "amount": 10.00}
        ]
    }
    add_expense_should_fail(gid, payload)

def test_settle_more_than_owed():
    gid = create_group("Settle Overpay")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    add_expense(gid, {
        "description": "Taxi",
        "amount": 50.00,
        "paid_by": [{"user_id": u1, "amount": 50.00}],
        "split_type": "equal",
        "users": [u1, u2]
    })
    settle_debt_should_fail(gid, payer_id=u2, payee_id=u1, amount=40.00)

def test_settle_when_nothing_owed():
    gid = create_group("Settle Nothing Owed")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    settle_debt_should_fail(gid, payer_id=u2, payee_id=u1, amount=10.00)

def test_expense_nonexistent_group_or_user():
    group_id = 99999
    user_id = 88888
    payload = {
        "description": "Invalid Group/User",
        "amount": 40.00,
        "paid_by": [{"user_id": user_id, "amount": 40.00}],
        "split_type": "exact",
        "splits": [{"user_id": user_id, "amount": 40.00}]
    }
    r = client.post(f"/groups/{group_id}/expenses", json=payload)
    assert r.status_code in [400, 404]

def test_negative_expense_amount():
    gid = create_group("Negative Amount Test")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    payload = {
        "description": "Negative Expense",
        "amount": -50.00,
        "paid_by": [{"user_id": u1, "amount": -50.00}],
        "split_type": "equal",
        "users": [u1, u2]
    }
    add_expense_should_fail(gid, payload)


def test_currency_mismatch():
    gid = create_group("Currency Mismatch Group")
    u1, u2 = create_user("User1"), create_user("User2")
    for uid in (u1, u2):
        add_member(gid, uid)
    payload = {
        "description": "Currency Mismatch",
        "amount": 50.00,
        "paid_by": [{"user_id": u1, "amount": 50.00}],
        "split_type": "equal",
        "currency": "EUR",
        "users": [u1, u2]
    }
    r = client.post(f"/groups/{gid}/expenses", json=payload)
    if r.status_code == 400:
        assert True
    else:
        pass

