# Expense Split Tracker

A backend API for managing group expenses, tracking who owes whom, settling debts, and automatically minimizing the number of transactions needed to settle up.

---

## 🚀 Features

- **Group Management:** Create groups for trips, events, or friends.
- **User Management:** Add users, invite members to groups.
- **Add Expenses with Split Logic:**
  - **Equal Split:** Divide expenses evenly.
  - **Exact Amount Split:** Assign a fixed amount per user.
  - **Percentage Split:** Split based on percentages.
- **Track Balances:**
  - Shows amounts owed and paid per user.
  - Provides a balance sheet for each user in a group.
- **Debt Settlement:**
  - Users can settle what they owe directly.
  - System updates balances to reflect settlements.
- **Debt Simplification:**
  - Automatically reduces the number of transactions needed—minimizing back-and-forth payments by finding the optimal settlements.
- **Validations:**
  - Prevents settling more than owed.
  - Ensures all expenses have compatible currencies.
  - Disallows negative/zero expense amounts.
  - Disallows adding expenses for non-existing users/groups.
  - Handles invalid split types and sums.
- **Edge Case Coverage:**
  - Currency mismatch.
  - Nonexistent group/user references.
  - Invalid split logic.
- **Comprehensive Testing:**
  - Included automated tests for all main features and edge cases.

---

## 🧑💻 API Endpoints

| Endpoint                               | Method | Description                      |
| -------------------------------------- | ------ | -------------------------------- |
| `/users`                               | POST   | Add a user                       |
| `/groups`                              | POST   | Create a group                   |
| `/groups/{group_id}/members`           | POST   | Add member to group              |
| `/groups/{group_id}/expenses`          | POST   | Add expense (with split logic)   |
| `/groups/{group_id}/expenses/balances` | GET    | Get balances for a group         |
| `/groups/{group_id}/settle`            | POST   | Settle a debt between two users  |
| `/groups/{group_id}/simplify`          | POST   | Automatically simplify all debts |

---

## 🧮 Split Types Supported

- **Equal Split:**  
  Expense divided evenly across all specified users.

- **Exact Amount Split:**  
  Each user is assigned a specific amount of the expense.

- **Percentage Split:**  
  Expense split by percentage per user.

---

## 💸 Debt Settlement & Simplification

- Debts can be settled individually (direct payment).
- The system prevents paying more than what’s owed.
- **Debt Simplification:**  
  Using a smart algorithm, the system finds the minimal set of transactions needed to clear up all group debts (i.e., if User A owes $30, User B owes $20, this gets optimized to just a single transaction).

---

## 🛡️ Validations & Edge Cases

- Expense amount must be positive.
- Splits/payments must match total and be non-negative.
- Only valid group/user IDs are accepted.
- Currency tracked and validated.
- All errors return informative messages.

---

## 🧪 Testing

- **Standard test cases:**
  - Equal split
  - Exact amount split
  - Percentage split
  - Settling debt
  - Debt simplification
- **Edge cases:**
  - Invalid split type
  - Mismatched split totals
  - Settling more than owed
  - Settling when nothing is owed
  - Expense with negative amount
  - Nonexistent group/user
  - Currency mismatch

Run all tests with:

```bash
pytest -v
```

---

## 🔧 Setup & Usage

1. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate your environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Use with Postman or automated tests!

---

## 🗂️ Data Model (Simplified Overview)

- **User:** Unique `id`, name, email.
- **Group:** Unique `id`, name.
- **GroupMember:** Connects users to groups.
- **Expense:** Includes split logic and tracks paid/shares.
- **ExpensePayer & ExpenseShare:** Record payment and breakdown.
- **Settlement:** Record who paid/received/how much.

---

## 🌟 Advanced (Optional Features)

- **Transaction history:** Easily extendable to show how debts and expenses evolved over time.
- **Dashboard via Postman:**  
  Demonstrates all core flows—group creation, adding expenses, viewing balances, settling and simplifying debts.

---

## 👨🎓 Author

Ajeet Kumar Shukla

---
