# Bank Account Simulation — Intermediate/Advanced Python

> Educational simulation only. This is **not** real banking software and must not be used for real financial transactions.

## Features

- Customer registration and secure PIN login
- PBKDF2-HMAC SHA-256 PIN hashing with random salt
- Multiple account types:
  - Savings — 4% simulated interest
  - Current — 0%
  - Fixed Deposit — 6.5% simulated interest
- Deposits and withdrawals
- Minimum-balance rules
- Customer authorization on transfers
- Account-to-account fund transfer
- Transaction history with timestamps
- Unique transaction IDs
- Interest calculation/application
- CSV transaction-history export
- JSON persistence
- Application/audit logging
- Custom exceptions
- Atomic-ish JSON replacement writes
- Modular service architecture

## Project structure

```text
bank_account_simulation/
├── main.py
├── README.md
├── data/
│   ├── customers.json
│   ├── accounts.json
│   └── transactions.json
├── exports/
├── logs/
│   └── bank.log
├── services/
│   ├── __init__.py
│   ├── bank_service.py
│   └── exceptions.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

## Requirements

Python 3.10+ recommended. No third-party packages are required.

## Run

```bash
cd bank_account_simulation
python main.py
```

## Suggested test flow

1. Register customer A.
2. Deposit money into the automatically created Savings account.
3. Create a Current account.
4. Deposit into it.
5. Transfer money between your own accounts.
6. Apply interest to Savings.
7. View transaction history.
8. Export the history to `exports/`.
9. Register customer B and test a transfer to B's account.
10. Try an incorrect PIN and an over-withdrawal to test validation.

## Security notes

The PIN is never stored as plaintext. A random salt and PBKDF2-HMAC-SHA256 with 200,000 iterations are used.

For a production banking application, additional protections would be required, including a real database, encryption at rest, secure session management, MFA, rate limiting/account lockout, CSRF protection, database transactions, key management, monitoring, backups, and regulatory controls.

## Architecture

`main.py` handles the CLI/UI.

`BankService` contains business rules and persistence operations.

`exceptions.py` defines domain-specific errors.

`helpers.py` contains small UI helpers.

JSON is used intentionally so the project remains beginner/intermediate friendly. A natural next upgrade is SQLite/PostgreSQL with repository classes and database transactions.
