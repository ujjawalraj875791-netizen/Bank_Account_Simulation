from datetime import datetime
from pathlib import Path
import csv
import json
import logging
import secrets
import hashlib
import hmac

from services.exceptions import (
    AuthenticationError, InsufficientFundsError, InvalidAmountError,
    AccountNotFoundError, AuthorizationError
)

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
EXPORTS = BASE / "exports"
LOGS = BASE / "logs"
DATA.mkdir(exist_ok=True); EXPORTS.mkdir(exist_ok=True); LOGS.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOGS / "bank.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

class BankService:
    RATES = {"Savings": 0.04, "Current": 0.00, "Fixed Deposit": 0.065}
    MIN_BALANCE = {"Savings": 500.0, "Current": 0.0, "Fixed Deposit": 5000.0}

    def __init__(self):
        self.customers_file = DATA / "customers.json"
        self.accounts_file = DATA / "accounts.json"
        self.transactions_file = DATA / "transactions.json"
        self._ensure_files()

    def _ensure_files(self):
        for f in [self.customers_file, self.accounts_file, self.transactions_file]:
            if not f.exists():
                f.write_text("[]", encoding="utf-8")

    def _read(self, file):
        return json.loads(file.read_text(encoding="utf-8"))

    def _write(self, file, data):
        temp = file.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp.replace(file)

    def _hash_pin(self, pin, salt=None):
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)
        return salt.hex(), digest.hex()

    def _verify_pin(self, pin, salt_hex, digest_hex):
        _, digest = self._hash_pin(pin, bytes.fromhex(salt_hex))
        return hmac.compare_digest(digest, digest_hex)

    def register_customer(self, name, phone, pin):
        if not name or not phone:
            raise ValueError("Name and phone are required.")
        if not pin.isdigit() or not 4 <= len(pin) <= 6:
            raise ValueError("PIN must contain 4-6 digits.")

        customers = self._read(self.customers_file)
        customer_id = "C" + secrets.token_hex(4).upper()
        salt, digest = self._hash_pin(pin)
        customer = {
            "customer_id": customer_id, "name": name, "phone": phone,
            "pin_salt": salt, "pin_hash": digest,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }
        customers.append(customer)
        self._write(self.customers_file, customers)

        account_no = self._create_account(customer_id, "Savings")
        logging.info("Customer registered: %s", customer_id)
        return f"Registration successful. Customer ID: {customer_id}. Savings account: {account_no}"

    def login(self, customer_id, pin):
        customers = self._read(self.customers_file)
        customer = next((c for c in customers if c["customer_id"] == customer_id), None)
        if not customer or not self._verify_pin(pin, customer["pin_salt"], customer["pin_hash"]):
            logging.warning("Failed login for %s", customer_id)
            raise AuthenticationError("Invalid customer ID or PIN.")
        logging.info("Successful login: %s", customer_id)
        return customer

    def _create_account(self, customer_id, account_type):
        accounts = self._read(self.accounts_file)
        no = "AC" + secrets.token_hex(5).upper()
        account = {
            "account_number": no, "customer_id": customer_id,
            "account_type": account_type, "balance": 0.0,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(timespec="seconds")
        }
        accounts.append(account)
        self._write(self.accounts_file, accounts)
        return no

    def create_account(self, customer_id):
        accounts = self._read(self.accounts_file)
        current = [a for a in accounts if a["customer_id"] == customer_id and a["status"] == "ACTIVE"]
        types = ["Savings", "Current", "Fixed Deposit"]
        print("Account types:")
        for i, t in enumerate(types, 1):
            print(f"{i}. {t}")
        choice = int(input("Select: ")) - 1
        if not 0 <= choice < len(types):
            raise ValueError("Invalid account type.")
        t = types[choice]
        no = self._create_account(customer_id, t)
        return f"{t} account created: {no}. Minimum balance: {self.MIN_BALANCE[t]:.2f}"

    def get_customer_accounts(self, customer_id):
        return [a for a in self._read(self.accounts_file)
                if a["customer_id"] == customer_id and a["status"] == "ACTIVE"]

    def _get_account(self, number):
        accounts = self._read(self.accounts_file)
        account = next((a for a in accounts if a["account_number"] == number and a["status"] == "ACTIVE"), None)
        if not account:
            raise AccountNotFoundError("Active account not found.")
        return accounts, account

    def _validate_amount(self, amount):
        if amount <= 0:
            raise InvalidAmountError("Amount must be greater than zero.")

    def _record(self, account_no, tx_type, amount, balance_after, description, related=None):
        txs = self._read(self.transactions_file)
        txs.append({
            "transaction_id": "TX" + secrets.token_hex(6).upper(),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "account_number": account_no, "transaction_type": tx_type,
            "amount": round(amount, 2), "balance_after": round(balance_after, 2),
            "description": description, "related_account": related
        })
        self._write(self.transactions_file, txs)

    def deposit(self, account_no, amount):
        self._validate_amount(amount)
        accounts, account = self._get_account(account_no)
        account["balance"] = round(account["balance"] + amount, 2)
        self._write(self.accounts_file, accounts)
        self._record(account_no, "DEPOSIT", amount, account["balance"], "Cash deposit")
        logging.info("Deposit %s %.2f", account_no, amount)
        return f"Deposited {amount:.2f}. New balance: {account['balance']:.2f}"

    def withdraw(self, account_no, amount):
        self._validate_amount(amount)
        accounts, account = self._get_account(account_no)
        minimum = self.MIN_BALANCE[account["account_type"]]
        if account["balance"] - amount < minimum:
            raise InsufficientFundsError(f"Withdrawal would violate minimum balance of {minimum:.2f}.")
        account["balance"] = round(account["balance"] - amount, 2)
        self._write(self.accounts_file, accounts)
        self._record(account_no, "WITHDRAW", amount, account["balance"], "Cash withdrawal")
        return f"Withdrawn {amount:.2f}. New balance: {account['balance']:.2f}"

    def transfer(self, customer_id, sender_no, receiver_no, amount):
        self._validate_amount(amount)
        if sender_no == receiver_no:
            raise ValueError("Sender and receiver must be different.")
        accounts = self._read(self.accounts_file)
        sender = next((a for a in accounts if a["account_number"] == sender_no and a["status"] == "ACTIVE"), None)
        receiver = next((a for a in accounts if a["account_number"] == receiver_no and a["status"] == "ACTIVE"), None)
        if not sender or not receiver:
            raise AccountNotFoundError("Sender or receiver account not found.")
        if sender["customer_id"] != customer_id:
            raise AuthorizationError("You can only transfer from your own account.")
        if sender["balance"] - amount < self.MIN_BALANCE[sender["account_type"]]:
            raise InsufficientFundsError("Insufficient transferable balance.")

        sender["balance"] = round(sender["balance"] - amount, 2)
        receiver["balance"] = round(receiver["balance"] + amount, 2)
        self._write(self.accounts_file, accounts)
        self._record(sender_no, "TRANSFER_OUT", amount, sender["balance"], f"Transfer to {receiver_no}", receiver_no)
        self._record(receiver_no, "TRANSFER_IN", amount, receiver["balance"], f"Transfer from {sender_no}", sender_no)
        logging.info("Transfer %.2f from %s to %s", amount, sender_no, receiver_no)
        return f"Transfer successful. New sender balance: {sender['balance']:.2f}"

    def apply_interest(self, account_no):
        accounts, account = self._get_account(account_no)
        rate = self.RATES[account["account_type"]]
        interest = round(account["balance"] * rate, 2)
        if interest <= 0:
            return "No interest applicable."
        account["balance"] = round(account["balance"] + interest, 2)
        self._write(self.accounts_file, accounts)
        self._record(account_no, "INTEREST", interest, account["balance"], f"Interest at {rate*100:.2f}%")
        return f"Interest {interest:.2f} applied at {rate*100:.2f}%. New balance: {account['balance']:.2f}"

    def get_transactions(self, account_no):
        self._get_account(account_no)
        return [t for t in self._read(self.transactions_file) if t["account_number"] == account_no]

    def export_transactions(self, account_no):
        rows = self.get_transactions(account_no)
        path = EXPORTS / f"{account_no}_transactions.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id","timestamp","account_number","transaction_type",
                "amount","balance_after","description","related_account"
            ])
            writer.writeheader()
            writer.writerows(rows)
        return f"Exported {len(rows)} transactions to {path}"
