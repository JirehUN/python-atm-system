import hashlib
import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MAX_PIN_ATTEMPTS = 3  # wrong PINs allowed before the account locks


# --------------------------------------------------------------------------
# Custom exceptions (main.py catches these to show friendly messages)
# --------------------------------------------------------------------------
class ATMError(Exception):
    """Base class for all ATM errors."""


class ValidationError(ATMError):
    """Bad input: invalid PIN format, bad amount, unknown account, etc."""


class AuthenticationError(ATMError):
    """Wrong account number or PIN, or not logged in."""


class AccountLockedError(ATMError):
    """Account is locked after too many failed PIN attempts."""


class InsufficientFundsError(ATMError):
    """Not enough money in the account."""


# --------------------------------------------------------------------------
# Account: one customer's account
# --------------------------------------------------------------------------
class Account:
    def __init__(self, account_number, holder_name, pin, balance=Decimal("0.00")):
        self._account_number = account_number
        self._holder_name = holder_name
        self._salt = secrets.token_hex(8)        # random salt per account
        self._pin_hash = self._hash_pin(pin)     # raw PIN is never stored
        self._balance = balance
        self._transactions = []                  # list of dicts
        self.failed_attempts = 0
        self.locked = False

    # Read-only properties (encapsulation: outside code can't edit them directly)
    @property
    def account_number(self):
        return self._account_number

    @property
    def holder_name(self):
        return self._holder_name

    @property
    def balance(self):
        return self._balance

    @property
    def transactions(self):
        return list(self._transactions)  # copy so callers can't change history

    # --- PIN handling ---
    def _hash_pin(self, pin):
        return hashlib.sha256((self._salt + pin).encode()).hexdigest()

    def verify_pin(self, pin):
        return secrets.compare_digest(self._hash_pin(pin), self._pin_hash)

    def set_pin(self, new_pin):
        self._pin_hash = self._hash_pin(new_pin)

    # --- Money handling (the Bank validates amounts before calling these) ---
    def _credit(self, amount):
        self._balance += amount

    def _debit(self, amount):
        if amount > self._balance:
            raise InsufficientFundsError("Insufficient funds.")
        self._balance -= amount

    def _record(self, tx_type, amount, note=""):
        """Add a timestamped entry to the transaction history."""
        self._transactions.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": tx_type,
            "amount": amount,
            "balance_after": self._balance,
            "note": note,
        })


# --------------------------------------------------------------------------
# Bank: manages all accounts
# --------------------------------------------------------------------------
class Bank:
    def __init__(self):
        self._accounts = {}  # account_number (str) -> Account

    # ---------- validation helpers ----------
    @staticmethod
    def _validate_pin(pin):
        if not (isinstance(pin, str) and len(pin) == 4 and pin.isdigit()):
            raise ValidationError("PIN must be exactly 4 digits.")

    @staticmethod
    def _parse_amount(value, allow_zero=False):
        """Turn input into a Decimal with 2 decimal places, or raise."""
        try:
            amount = Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            raise ValidationError("Amount must be a number.")
        if not amount.is_finite():
            raise ValidationError("Amount must be a number.")
        if amount < 0 or (amount == 0 and not allow_zero):
            raise ValidationError("Amount must be greater than zero.")
        return amount

    @staticmethod
    def _validate_account_number(number):
        if not (isinstance(number, str) and number.isdigit()):
            raise ValidationError("Account number must contain digits only.")

    def _get_account(self, number):
        self._validate_account_number(number)
        account = self._accounts.get(number)
        if account is None:
            raise ValidationError("Account does not exist.")
        return account

    def _generate_account_number(self):
        """Random 10-digit number, regenerated until it is unique."""
        while True:
            number = "20" + str(secrets.randbelow(10 ** 8)).zfill(8)
            if number not in self._accounts:
                return number

    # ---------- public operations ----------
    def create_account(self, name, pin, initial_deposit=0):
        """Create an account and return its new account number."""
        name = (name or "").strip()
        if not name:
            raise ValidationError("Name cannot be empty.")
        self._validate_pin(pin)
        initial = self._parse_amount(initial_deposit, allow_zero=True)

        number = self._generate_account_number()
        account = Account(number, name, pin)
        if initial > 0:
            account._credit(initial)
            account._record("DEPOSIT", initial, "Initial deposit")
        self._accounts[number] = account
        return number

    def login(self, account_number, pin):
        """Check credentials. Returns the account number on success."""
        self._validate_account_number(account_number)
        account = self._accounts.get(account_number)
        # Same message for unknown account / wrong PIN so nothing is leaked
        if account is None:
            raise AuthenticationError("Invalid account number or PIN.")
        self._check_pin(account, pin)
        return account.account_number

    def _check_pin(self, account, pin):
        """Verify PIN, count failures, lock the account after too many."""
        if account.locked:
            raise AccountLockedError("This account is locked. Please contact the bank.")
        if isinstance(pin, str) and account.verify_pin(pin):
            account.failed_attempts = 0
            return
        account.failed_attempts += 1
        if account.failed_attempts >= MAX_PIN_ATTEMPTS:
            account.locked = True
            raise AccountLockedError("Too many wrong PINs. Account is now locked.")
        left = MAX_PIN_ATTEMPTS - account.failed_attempts
        raise AuthenticationError(f"Invalid account number or PIN. {left} attempt(s) left.")

    def check_balance(self, account_number):
        return self._get_account(account_number).balance

    def deposit(self, account_number, amount):
        account = self._get_account(account_number)
        amount = self._parse_amount(amount)
        account._credit(amount)
        account._record("DEPOSIT", amount)
        return account.balance

    def withdraw(self, account_number, amount):
        account = self._get_account(account_number)
        amount = self._parse_amount(amount)
        account._debit(amount)  # raises InsufficientFundsError if too much
        account._record("WITHDRAWAL", amount)
        return account.balance

    def transfer(self, from_number, to_number, amount):
        """Move money between two accounts. Returns sender's new balance."""
        sender = self._get_account(from_number)
        self._validate_account_number(to_number)
        if from_number == to_number:
            raise ValidationError("You cannot transfer to your own account.")
        receiver = self._accounts.get(to_number)
        if receiver is None:
            raise ValidationError("Destination account does not exist.")
        amount = self._parse_amount(amount)

        sender._debit(amount)       # fails first if funds are short, nothing changes
        receiver._credit(amount)
        sender._record("TRANSFER OUT", amount, f"To {to_number}")
        receiver._record("TRANSFER IN", amount, f"From {from_number}")
        return sender.balance

    def get_history(self, account_number):
        return self._get_account(account_number).transactions

    def change_pin(self, account_number, old_pin, new_pin):
        account = self._get_account(account_number)
        self._validate_pin(new_pin)
        self._check_pin(account, old_pin)  # wrong old PIN counts as a failed attempt
        if old_pin == new_pin:
            raise ValidationError("New PIN must be different from the old PIN.")
        account.set_pin(new_pin)
        account._record("PIN CHANGE", Decimal("0.00"), "PIN updated")

    def get_holder_name(self, account_number):
        return self._get_account(account_number).holder_name


# --------------------------------------------------------------------------
# ATM: a login session on top of the Bank (keeps main.py simple)
# --------------------------------------------------------------------------
class ATM:
    def __init__(self, bank):
        self._bank = bank
        self._current = None  # account number of the logged-in user

    @property
    def logged_in(self):
        return self._current is not None

    @property
    def account_number(self):
        return self._current

    @property
    def holder_name(self):
        return self._bank.get_holder_name(self._require_login())

    def _require_login(self):
        if self._current is None:
            raise AuthenticationError("Please log in first.")
        return self._current

    def login(self, account_number, pin):
        self._current = self._bank.login(account_number, pin)

    def logout(self):
        self._current = None

    def balance(self):
        return self._bank.check_balance(self._require_login())

    def deposit(self, amount):
        return self._bank.deposit(self._require_login(), amount)

    def withdraw(self, amount):
        return self._bank.withdraw(self._require_login(), amount)

    def transfer(self, to_number, amount):
        return self._bank.transfer(self._require_login(), to_number, amount)

    def history(self):
        return self._bank.get_history(self._require_login())

    def change_pin(self, old_pin, new_pin):
        self._bank.change_pin(self._require_login(), old_pin, new_pin)
    