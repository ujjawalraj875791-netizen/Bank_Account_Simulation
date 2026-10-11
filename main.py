from services.bank_service import BankService
from utils.helpers import clear_screen, pause, money

def account_menu(bank, user):
    while True:
        clear_screen()
        print("=== ACCOUNT MENU ===")
        print(f"Welcome, {user['name']} | Customer ID: {user['customer_id']}")
        print("1. View accounts")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Transfer funds")
        print("5. Calculate/apply interest")
        print("6. View transaction history")
        print("7. Export transaction history")
        print("8. Create account")
        print("9. Logout")
        choice = input("\nChoose: ").strip()

        try:
            if choice == "1":
                accounts = bank.get_customer_accounts(user["customer_id"])
                for a in accounts:
                    print(f"\n{a['account_number']} | {a['account_type']} | Balance: {money(a['balance'])}")
                    print(f"Status: {a['status']}")
                pause()
            elif choice in {"2", "3", "5", "6", "7"}:
                accounts = bank.get_customer_accounts(user["customer_id"])
                if not accounts:
                    print("No accounts found."); pause(); continue
                for i, a in enumerate(accounts, 1):
                    print(f"{i}. {a['account_number']} - {a['account_type']} - {money(a['balance'])}")
                idx = int(input("Select account: ")) - 1
                account_no = accounts[idx]["account_number"]

                if choice == "2":
                    amount = float(input("Deposit amount: "))
                    print(bank.deposit(account_no, amount))
                elif choice == "3":
                    amount = float(input("Withdrawal amount: "))
                    print(bank.withdraw(account_no, amount))
                elif choice == "5":
                    print(bank.apply_interest(account_no))
                elif choice == "6":
                    rows = bank.get_transactions(account_no)
                    print("\n".join(
                        f"{r['timestamp']} | {r['transaction_type']} | {money(r['amount'])} | "
                        f"Balance: {money(r['balance_after'])} | {r['description']}"
                        for r in rows
                    ) or "No transactions.")
                elif choice == "7":
                    print(bank.export_transactions(account_no))
                pause()
            elif choice == "4":
                sender = input("Sender account number: ").strip()
                receiver = input("Receiver account number: ").strip()
                amount = float(input("Amount: "))
                print(bank.transfer(user["customer_id"], sender, receiver, amount))
                pause()
            elif choice == "8":
                print(bank.create_account(user["customer_id"]))
                pause()
            elif choice == "9":
                return
            else:
                print("Invalid choice."); pause()
        except (ValueError, IndexError) as e:
            print(f"Invalid input: {e}"); pause()
        except Exception as e:
            print(f"Operation failed: {e}"); pause()

def main():
    bank = BankService()
    while True:
        clear_screen()
        print("===================================")
        print("     BANK ACCOUNT SIMULATION")
        print("===================================")
        print("1. Register customer")
        print("2. Login")
        print("3. Exit")
        choice = input("\nChoose: ").strip()

        try:
            if choice == "1":
                name = input("Full name: ").strip()
                phone = input("Phone: ").strip()
                pin = input("Create 4-6 digit PIN: ").strip()
                print(bank.register_customer(name, phone, pin))
                pause()
            elif choice == "2":
                customer_id = input("Customer ID: ").strip()
                pin = input("PIN: ").strip()
                user = bank.login(customer_id, pin)
                print(f"Login successful. Welcome {user['name']}.")
                pause()
                account_menu(bank, user)
            elif choice == "3":
                print("Thank you for using the simulation.")
                break
            else:
                print("Invalid choice."); pause()
        except Exception as e:
            print(f"Error: {e}"); pause()

if __name__ == "__main__":
    main()
