Python ATM Machine System

A beginner-friendly, terminal-based ATM simulation written in Python using object-oriented programming. Customers can create accounts, log in with a PIN, and manage their money from a simple text menu.

What It Does

The program simulates a bank and an ATM. Everything runs in memory, so all accounts and transactions reset when the program closes.

Features
Create account: register with a name, a 4-digit PIN and an optional initial deposit. A unique 10-digit account number is generated automatically.
Login: access your account with your account number and PIN. The PIN is hidden while you type.
Check balance: see your current balance.
Deposit: add money to your account.
Withdraw: take money out, with a check for insufficient funds.
Transfer: send money to another account (you can't transfer to yourself or to an account that doesn't exist).
Transaction history: a timestamped list of every deposit, withdrawal, transfer and PIN change.
Change PIN: update your PIN after confirming the current one.
Account lock: after 3 wrong PIN attempts the account is locked.
Safe input handling: invalid menu choices, non-numeric amounts, negative amounts and Ctrl+C are handled without crashing.

Project Structure
File	  Purpose
class.py	Backend logic: Account, Bank and ATM classes plus custom exceptions. It never prints anything.
main.py	Terminal frontend: menus, input and output. It calls the backend and shows results or error messages.

Requirements

Python 3.8 or newer (developed and run on Python 3.14)
No external dependencies. It only uses the standard library: hashlib, secrets, decimal, datetime, getpass and importlib.
How to Run
Put class.py and main.py in the same folder.
Open a terminal (PowerShell, Command Prompt or any shell) in that folder.

What I Learned
1. Separating logic from interface: keeping the backend (class.py) free of print and input meant the same logic could be tested without the menu and reused with any other interface.
2. Encapsulation: private attributes and read-only properties stop outside code from changing a balance or reading a PIN directly.
3. Custom exceptions: ValidationError, AuthenticationError, AccountLockedError and InsufficientFundsError let the frontend show friendly messages instead of crashing.
4. Reserved keywords: class can't be used in import class. The fix is importlib.import_module("class"). A better choice would have been a different file name such as bank.py.
5. Python's import path: a script only looks for modules in its own folder, so class.py must sit next to main.py.
6. Hashing and salting: why PINs are hashed instead of stored, and how a random salt makes identical PINs produce different hashes.
7. Money needs Decimal: floats cause rounding errors like 0.1 + 0.2, so balances use Decimal rounded to 2 places.
8. Validate before changing anything: in a transfer, the sender is checked for funds before any money moves, so a failure never leaves the accounts half-updated.
9. Testing without the menu: calling backend methods directly in a short script made it quick to check edge cases like a locked account or an overdraft.

Possible Improvements
1. Save accounts to a JSON file or database so data persists
2. Add a daily withdrawal limit
3. Add an admin option to unlock accounts
4. Build a GUI or web interface on top of the same backend
