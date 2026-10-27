import importlib
from getpass import getpass


atm_backend = importlib.import_module("class")

LINE = "=" * 44


def money(value):
    """Format a Decimal like 1,250.50"""
    return f"{value:,.2f}"


def ask(prompt):
    """Normal text input, stripped of spaces."""
    return input(prompt).strip()


def ask_pin(prompt="Enter 4-digit PIN: "):
    """PIN input that is hidden while typing."""
    return getpass(prompt)


def ask_amount(prompt):
    """Ask for a number. Returns a string (backend validates it fully)
    or None if the user typed something that is not a number."""
    text = ask(prompt)
    try:
        float(text)  # quick check so we can say "enter a number" early
    except ValueError:
        print("  Please enter a valid number.")
        return None
    return text


def banner():
    print(LINE)
    print("      WELCOME TO THE PYTHON ATM SYSTEM")
    print(LINE)


# --------------------------------------------------------------------------
# Main (logged-out) menu actions
# --------------------------------------------------------------------------
def create_account(bank):
    print("\n--- Create Account ---")
    name = ask("Full name: ")
    pin = ask_pin("Choose a 4-digit PIN: ")
    confirm = ask_pin("Confirm PIN: ")
    if pin != confirm:
        print("  PINs do not match. Account not created.")
        return
    deposit = ask("Initial deposit (press Enter for 0): ") or "0"
    number = bank.create_account(name, pin, deposit)
    print(f"\n  Account created! Your account number is: {number}")
    print("  Keep it safe - you need it to log in.")


def login(bank, atm):
    print("\n--- Login ---")
    number = ask("Account number: ")
    pin = ask_pin()
    atm.login(number, pin)
    print(f"\n  Welcome, {atm.holder_name}!")



# Logged-in menu actions

def show_balance(atm):
    print(f"\n  Current balance: {money(atm.balance())}")


def do_deposit(atm):
    amount = ask_amount("Amount to deposit: ")
    if amount is None:
        return
    new_balance = atm.deposit(amount)
    print(f"\n  Deposit successful. New balance: {money(new_balance)}")


def do_withdraw(atm):
    amount = ask_amount("Amount to withdraw: ")
    if amount is None:
        return
    new_balance = atm.withdraw(amount)
    print(f"\n  Please take your cash. New balance: {money(new_balance)}")


def do_transfer(atm):
    to_number = ask("Destination account number: ")
    amount = ask_amount("Amount to transfer: ")
    if amount is None:
        return
    new_balance = atm.transfer(to_number, amount)
    print(f"\n  Transfer successful. New balance: {money(new_balance)}")


def show_history(atm):
    history = atm.history()
    print("\n--- Transaction History ---")
    if not history:
        print("  No transactions yet.")
        return
    for tx in history:
        note = f"  ({tx['note']})" if tx["note"] else ""
        print(f"  {tx['timestamp']}  {tx['type']:<13} "
              f"{money(tx['amount']):>12}  Bal: {money(tx['balance_after']):>12}{note}")


def do_change_pin(atm):
    old_pin = ask_pin("Current PIN: ")
    new_pin = ask_pin("New 4-digit PIN: ")
    confirm = ask_pin("Confirm new PIN: ")
    if new_pin != confirm:
        print("  New PINs do not match. PIN not changed.")
        return
    atm.change_pin(old_pin, new_pin)
    print("\n  PIN changed successfully.")


def account_menu(atm):
    """Menu shown after login. Returns when the user logs out."""
    actions = {
        "1": ("Check Balance", lambda: show_balance(atm)),
        "2": ("Deposit", lambda: do_deposit(atm)),
        "3": ("Withdraw", lambda: do_withdraw(atm)),
        "4": ("Transfer", lambda: do_transfer(atm)),
        "5": ("Transaction History", lambda: show_history(atm)),
        "6": ("Change PIN", lambda: do_change_pin(atm)),
    }
    while atm.logged_in:
        print(f"\n{LINE}\n  ACCOUNT MENU  (Acct {atm.account_number})\n{LINE}")
        for key, (label, _) in actions.items():
            print(f"  {key}. {label}")
        print("  7. Logout")

        choice = ask("Choose an option (1-7): ")
        if choice == "7":
            atm.logout()
            print("\n  Logged out. Thank you for banking with us!")
        elif choice in actions:
            try:
                actions[choice][1]()
            except atm_backend.ATMError as error:
                print(f"\n  Error: {error}")
                # A locked account is logged out for safety
                if isinstance(error, atm_backend.AccountLockedError):
                    atm.logout()
        else:
            print("  Invalid choice. Please enter a number from 1 to 7.")



# Program entry

def main():
    bank = atm_backend.Bank()
    atm = atm_backend.ATM(bank)
    banner()

    try:
        while True:
            print("\nMAIN MENU")
            print("  1. Create Account")
            print("  2. Login")
            print("  3. Exit")
            choice = ask("Choose an option (1-3): ")

            try:
                if choice == "1":
                    create_account(bank)
                elif choice == "2":
                    login(bank, atm)
                    account_menu(atm)
                elif choice == "3":
                    print("\nGoodbye!")
                    break
                else:
                    print("  Invalid choice. Please enter 1, 2 or 3.")
            except atm_backend.ATMError as error:
                print(f"\n  Error: {error}")
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C or Ctrl+Z/Ctrl+D: leave cleanly instead of showing a traceback
        print("\n\nSession ended. Goodbye!")


if __name__ == "__main__":
    main()