# AtmProgramPY
---

# Enhanced ATM Simulation Program

![ATM Banner](https://via.placeholder.com/800x200.png?text=Enhanced+ATM+Simulation+Program)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Code Structure](#code-structure)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Overview
This repository contains an ATM simulation program written in Python. The simulation models common banking operations such as balance inquiries, withdrawals, deposits, transfers, PIN changes, and even simulates interest accrual. The program uses a modern, interactive command-line interface (CLI) powered by the [Rich](https://rich.readthedocs.io) library for an engaging user experience.

The program is designed with modularity and scalability in mind. It features robust error handling, detailed logging via a rotating file handler, and an object-oriented architecture that makes it easy to extend or integrate with other systems.

## Features
- **User Authentication:** Secure login using hashed PINs.
- **Transaction Processing:** Supports withdrawals, deposits, transfers, and interest accrual.
- **Daily Limits:** Implements daily transaction limits and caching for efficiency.
- **Enhanced UI:** Uses the Rich library for colored, tabular, and panel-based output.
- **Logging:** Logs all operations with a rotating file handler to avoid oversized logs.
- **PIN Management:** Allows users to change their PIN securely.
- **Robust Error Handling:** Catches and logs errors for ease of debugging.
- **Extensible:** Structured in a modular fashion, making it easy to add more features.

## Installation

### Prerequisites
- **Python 3.8+** is recommended.
- **Pip** – Python package installer.

### Steps
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/atm-simulation.git
   cd atm-simulation
   ```

2. **Create a Virtual Environment (Optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Required Dependencies:**
   The program requires the `rich` library. Install it with:
   ```bash
   pip install rich
   ```

4. **(Optional) Install Other Dependencies:**
   If additional dependencies are needed, add them to a `requirements.txt` file and install:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
To run the ATM simulation program, execute the main Python file:
```bash
python atm_simulation.py
```

Upon running, you will be presented with a modern, interactive menu. You can choose options to check your balance, withdraw, deposit, transfer funds, view transaction history, change your PIN, simulate interest accrual, or log out.

### Example Session:
1. **Login:**  
   You will be prompted for a username and PIN. Default test accounts are preloaded (e.g., `ATA` with PIN `8830`).

2. **Menu Options:**
   - **1:** Check balance.
   - **2:** Withdraw funds.
   - **3:** Deposit funds.
   - **4:** Transfer funds to another account.
   - **5:** View transaction history.
   - **6:** Change your PIN.
   - **7:** Simulate interest accrual.
   - **8:** Logout.
   - **9:** Exit the program.

## Code Structure
Below is an overview of the main components in the program:

### `Transaction` Dataclass
Defines a structure for recording transactions:
- **Attributes:**
  - `timestamp`: Date and time of the transaction.
  - `type`: Type of transaction (e.g., withdrawal, deposit).
  - `amount`: The amount involved.
  - `balance_after`: Account balance after the transaction.
  - `recipient`: (Optional) The recipient account in case of transfers.
- **Methods:**
  - `to_dict()`: Converts the transaction into a dictionary for logging and display.

### `SecurityError` Exception
A custom exception used to signal security-related issues (e.g., operations attempted without an active session).

### `ATMSystem` Class
Encapsulates the core ATM functionality:
- **Initialization:**
  - Sets up logging with a rotating file handler.
  - Loads initial account data.
  - Initializes various attributes like daily totals, transaction history, and failed login attempts.
- **Key Methods:**
  - `setup_logging()`: Configures the logging mechanism.
  - `_load_initial_data()`: Loads user account data, hashing the PINs.
  - `authenticate()`: Authenticates users with a retry limit and a cooldown period.
  - `_handle_failed_attempt()`: Updates and tracks failed login attempts.
  - `check_balance()`: Retrieves the current account balance.
  - `_update_daily_total()` & `_get_daily_total()`: Manage daily limits for transactions.
  - `withdraw()`, `deposit()`, `transfer()`: Process banking transactions.
  - `change_pin()`: Allows the user to change their PIN.
  - `simulate_interest()`: Simulates interest accrual on the current balance.
  - `get_transaction_history()`: Retrieves a history of transactions.
  - `logout()`: Ends the user session.

### Main Program (`main()` Function)
Handles the CLI interactions:
- Uses the **Rich** library to create a modern, interactive interface.
- Presents a menu with available operations.
- Processes user inputs and calls corresponding methods from the `ATMSystem` class.
- Provides error messages and feedback using colorized output panels.

## Dependencies
- [Rich](https://rich.readthedocs.io): For an enhanced command-line interface.
- Standard Python libraries: `logging`, `datetime`, `hashlib`, `decimal`, `typing`, `json`, and `dataclasses`.

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes with clear commit messages.
4. Submit a pull request.

Please ensure that your code adheres to the existing style and that you update the documentation accordingly.

## License
This project is licensed under the [MIT License](LICENSE).

## Acknowledgments
- The **Rich** library for making the CLI interface more attractive and interactive.
- Contributors and testers who provided feedback to improve this simulation.

---

## Complete Source Code

Below is the complete source code for the ATM simulation program:

```python
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, date
import hashlib
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, Dict, List
import json
from dataclasses import dataclass, asdict

# Importing Rich for an enhanced user interface
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


@dataclass
class Transaction:
    """
    A dataclass representing a banking transaction.
    
    Attributes:
        timestamp (datetime): The time when the transaction occurred.
        type (str): The type of the transaction (e.g., withdrawal, deposit, transfer).
        amount (Decimal): The amount involved in the transaction.
        balance_after (Decimal): The account balance after the transaction.
        recipient (Optional[str]): The recipient account for transfers.
    """
    timestamp: datetime
    type: str
    amount: Decimal
    balance_after: Decimal
    recipient: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the Transaction to a dictionary for logging and display."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["amount"] = str(self.amount)
        data["balance_after"] = str(self.balance_after)
        return data


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class ATMSystem:
    """
    Represents an ATM system with user accounts and transaction processing.

    Methods:
        authenticate: Validates user credentials.
        check_balance: Returns the current account balance.
        withdraw: Processes a withdrawal transaction.
        deposit: Processes a deposit transaction.
        transfer: Transfers funds between accounts.
        change_pin: Changes the user's PIN.
        simulate_interest: Simulates interest accrual on the account balance.
        get_transaction_history: Retrieves the transaction history.
        logout: Ends the current user session.
    """
    def __init__(self, initial_data: list = None):
        """Initialize the ATM system with user data and setup logging."""
        self.setup_logging()  # Setup the logger first
        # Initialize attributes required before loading data.
        self.daily_totals: Dict[str, Dict[str, Dict[date, Decimal]]] = {}
        self.accounts: Dict[str, Dict[str, Decimal or str]] = {}
        self._load_initial_data(initial_data)
        self.transaction_history: Dict[str, List[Transaction]] = {}
        self.failed_attempts: Dict[str, Tuple[int, datetime]] = {}
        self.session_active: bool = False
        self.current_user: Optional[str] = None

    def setup_logging(self):
        """Configure the logging system with a rotating file handler."""
        self.logger = logging.getLogger("ATMSystem")
        self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler("atm_transactions.log", maxBytes=5 * 1024 * 1024, backupCount=3)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def _load_initial_data(self, initial_data: list = None):
        """Load initial user data or create default data."""
        if initial_data is None:
            initial_data = [
                ('ATA', self._hash_password('8830'), Decimal('100000')),
                ('AISYAH', self._hash_password('8790'), Decimal('50000')),
                ('EZRA DEBY', self._hash_password('9086'), Decimal('200000'))
            ]
        for username, pw_hash, saldo in initial_data:
            key = username.strip().upper()
            self.accounts[key] = {'password_hash': pw_hash, 'saldo': saldo}
            # Initialize daily totals for each account
            self.daily_totals[key] = {'withdrawal': {}, 'deposit': {}, 'transfer': {}}

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.strip().encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate a user using their username and PIN.
        
        Implements a cooldown mechanism after multiple failed attempts.
        """
        username = username.strip().upper()

        # Check for too many failed attempts (cooling period: 5 minutes)
        if username in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[username]
            if attempts >= 3:
                time_diff = (datetime.now() - last_attempt).total_seconds()
                if time_diff < 300:
                    self.logger.warning(f"Account {username} locked due to multiple failed attempts")
                    console.print(f"[bold red]Account locked. Please try again in {int(5 - time_diff // 60)} minutes[/bold red]")
                    return False
                else:
                    self.failed_attempts[username] = (0, datetime.now())

        if username not in self.accounts:
            self.logger.warning(f"Failed login attempt for non-existent user: {username}")
            console.print("[bold red]User not found.[/bold red]")
            return False

        stored_hash = self.accounts[username]['password_hash']
        if self._hash_password(password) == stored_hash:
            self.failed_attempts[username] = (0, datetime.now())
            self.session_active = True
            self.current_user = username
            self.logger.info(f"Successful login: {username}")
            return True
        else:
            self._handle_failed_attempt(username)
            return False

    def _handle_failed_attempt(self, username: str):
        """Handle a failed login attempt and update the attempt counter."""
        if username in self.failed_attempts:
            attempts, _ = self.failed_attempts[username]
            attempts += 1
            self.failed_attempts[username] = (attempts, datetime.now())
        else:
            self.failed_attempts[username] = (1, datetime.now())

        attempts = self.failed_attempts[username][0]
        remaining = max(0, 3 - attempts)
        console.print(f"[bold red]Login failed. {remaining} attempt(s) remaining before temporary lockout.[/bold red]")

    def _assert_session(self):
        """Ensure that there is an active session before performing sensitive operations."""
        if not self.session_active or self.current_user is None:
            raise SecurityError("No active session")

    def check_balance(self) -> Decimal:
        """Return the current balance of the active user's account."""
        self._assert_session()
        return self.accounts[self.current_user]['saldo']

    def _update_daily_total(self, trans_type: str, amount: Decimal):
        """
        Update the daily total for a specific type of transaction.

        Args:
            trans_type (str): Type of transaction (withdrawal, deposit, transfer).
            amount (Decimal): The amount to add.
        """
        today = date.today()
        user_totals = self.daily_totals[self.current_user][trans_type]
        user_totals[today] = user_totals.get(today, Decimal('0')) + amount

    def _get_daily_total(self, trans_type: str) -> Decimal:
        """
        Retrieve the total amount transacted for a given type on the current day.
        
        Args:
            trans_type (str): The transaction type.
        """
        today = date.today()
        return self.daily_totals[self.current_user][trans_type].get(today, Decimal('0'))

    def _log_transaction(self, trans: Transaction):
        """
        Log a transaction both in memory and to the logging system.

        Args:
            trans (Transaction): The transaction to log.
        """
        if self.current_user not in self.transaction_history:
            self.transaction_history[self.current_user] = []
        self.transaction_history[self.current_user].append(trans)
        self.logger.info(f"Transaction: {self.current_user} - {json.dumps(trans.to_dict())}")

    def withdraw(self, amount: Decimal) -> Tuple[bool, str]:
        """
        Process a withdrawal request after validating the amount and daily limits.

        Returns:
            A tuple containing a boolean success flag and a message.
        """
        self._assert_session()
        try:
            amount = Decimal(amount)
        except (InvalidOperation, ValueError):
            return False, "Invalid amount"

        if amount <= 0:
            return False, "Amount must be positive"
        if amount % Decimal('50000') != 0:
            return False, "Amount must be in multiples of 50,000"

        current_balance = self.check_balance()
        if amount > current_balance:
            return False, "Insufficient funds"

        daily_limit = Decimal('5000000')
        if self._get_daily_total('withdrawal') + amount > daily_limit:
            return False, f"Daily withdrawal limit (Rp{daily_limit:,}) exceeded"

        self.accounts[self.current_user]['saldo'] -= amount
        self._update_daily_total('withdrawal', amount)
        trans = Transaction(
            timestamp=datetime.now(),
            type='withdrawal',
            amount=amount,
            balance_after=self.check_balance()
        )
        self._log_transaction(trans)
        return True, f"Successfully withdrawn Rp{amount:,}"

    def deposit(self, amount: Decimal) -> Tuple[bool, str]:
        """
        Process a deposit request after validating the amount.

        Returns:
            A tuple containing a boolean success flag and a message.
        """
        self._assert_session()
        try:
            amount = Decimal(amount)
        except (InvalidOperation, ValueError):
            return False, "Invalid amount"

        if amount <= 0:
            return False, "Amount must be positive"

        self.accounts[self.current_user]['saldo'] += amount
        self._update_daily_total('deposit', amount)
        trans = Transaction(
            timestamp=datetime.now(),
            type='deposit',
            amount=amount,
            balance_after=self.check_balance()
        )
        self._log_transaction(trans)
        return True, f"Successfully deposited Rp{amount:,}"

    def transfer(self, recipient: str, amount: Decimal) -> Tuple[bool, str]:
        """
        Process a funds transfer between the active user's account and another account.

        Returns:
            A tuple containing a boolean success flag and a message.
        """
        self._assert_session()
        recipient = recipient.strip().upper()

        if recipient not in self.accounts:
            return False, "Recipient account not found"
        if recipient == self.current_user:
            return False, "Cannot transfer to your own account"

        success, message = self.withdraw(amount)
        if not success:
            return False, message

        self.accounts[recipient]['saldo'] += amount
        self._update_daily_total('transfer', amount)
        trans = Transaction(
            timestamp=datetime.now(),
            type='transfer',
            amount=amount,
            balance_after=self.check_balance(),
            recipient=recipient
        )
        self._log_transaction(trans)
        return True, f"Successfully transferred Rp{amount:,} to {recipient}"

    def change_pin(self, old_pin: str, new_pin: str) -> Tuple[bool, str]:
        """
        Allow the current user to change their PIN.

        Returns:
            A tuple containing a boolean success flag and a message.
        """
        self._assert_session()
        if self._hash_password(old_pin) != self.accounts[self.current_user]['password_hash']:
            return False, "Incorrect old PIN"
        self.accounts[self.current_user]['password_hash'] = self._hash_password(new_pin)
        self.logger.info(f"User {self.current_user} changed PIN.")
        return True, "PIN successfully changed."

    def simulate_interest(self, interest_rate: Decimal = Decimal("0.01")) -> Tuple[bool, str]:
        """
        Simulate monthly interest accrual on the account balance.

        Returns:
            A tuple containing a boolean success flag and a message.
        """
        self._assert_session()
        current_balance = self.check_balance()
        interest = current_balance * interest_rate
        self.accounts[self.current_user]['saldo'] += interest
        trans = Transaction(
            timestamp=datetime.now(),
            type='interest',
            amount=interest,
            balance_after=self.check_balance()
        )
        self._log_transaction(trans)
        return True, f"Interest of Rp{interest:,.2f} applied. New balance: Rp{self.accounts[self.current_user]['saldo']:,.2f}"

    def get_transaction_history(self) -> List[dict]:
        """
        Retrieve the transaction history for the current user.

        Returns:
            A list of dictionaries representing transactions.
        """
        self._assert_session()
        return [trans.to_dict() for trans in self.transaction_history.get(self.current_user, [])]

    def logout(self):
        """End the current user session."""
        if self.session_active:
            self.logger.info(f"User logged out: {self.current_user}")
            self.session_active = False
            self.current_user = None


def main():
    """Main function to run the ATM simulation program."""
    atm = ATMSystem()
    console.print(Panel("[bold cyan]Welcome to the Enhanced ATM System[/bold cyan]", expand=False))
    
    while True:
        if not atm.session_active:
            username = Prompt.ask("[bold yellow]Enter username (or type 'exit' to quit)[/bold yellow]").strip()
            if username.lower() == 'exit':
                console.print("[bold green]Exiting... Goodbye![/bold green]")
                break
            password = Prompt.ask("[bold yellow]Enter PIN[/bold yellow]", password=True).strip()
            if not atm.authenticate(username, password):
                continue
            console.print(Panel("[bold green]Login successful![/bold green]", expand=False))
        
        # Build a modern menu using Rich's Table
        menu_table = Table(title="ATM Main Menu", show_header=False, header_style="bold magenta")
        menu_table.add_column("Option", justify="center", style="cyan", no_wrap=True)
        menu_table.add_column("Operation", style="magenta")
        menu_table.add_row("1", "Check Balance")
        menu_table.add_row("2", "Withdraw")
        menu_table.add_row("3", "Deposit")
        menu_table.add_row("4", "Transfer")
        menu_table.add_row("5", "Transaction History")
        menu_table.add_row("6", "Change PIN")
        menu_table.add_row("7", "Simulate Interest Accrual")
        menu_table.add_row("8", "Logout")
        menu_table.add_row("9", "Exit")
        console.print(menu_table)

        try:
            choice = Prompt.ask("[bold yellow]Select option (1-9)[/bold yellow]").strip()
            if choice == "1":
                balance = atm.check_balance()
                console.print(f"[bold green]Current balance: Rp{balance:,}[/bold green]")
            
            elif choice == "2":
                amt_input = Prompt.ask("[bold yellow]Enter amount to withdraw[/bold yellow]").strip()
                try:
                    amount = Decimal(amt_input)
                except (InvalidOperation, ValueError):
                    console.print("[bold red]Invalid amount[/bold red]")
                    continue
                success, message = atm.withdraw(amount)
                console.print(f"[bold blue]{message}[/bold blue]")
            
            elif choice == "3":
                amt_input = Prompt.ask("[bold yellow]Enter amount to deposit[/bold yellow]").strip()
                try:
                    amount = Decimal(amt_input)
                except (InvalidOperation, ValueError):
                    console.print("[bold red]Invalid amount[/bold red]")
                    continue
                success, message = atm.deposit(amount)
                console.print(f"[bold blue]{message}[/bold blue]")
            
            elif choice == "4":
                recipient = Prompt.ask("[bold yellow]Enter recipient username[/bold yellow]").strip()
                amt_input = Prompt.ask("[bold yellow]Enter amount to transfer[/bold yellow]").strip()
                try:
                    amount = Decimal(amt_input)
                except (InvalidOperation, ValueError):
                    console.print("[bold red]Invalid amount[/bold red]")
                    continue
                success, message = atm.transfer(recipient, amount)
                console.print(f"[bold blue]{message}[/bold blue]")
            
            elif choice == "5":
                history = atm.get_transaction_history()
                if not history:
                    console.print("[bold red]No transaction history available[/bold red]")
                else:
                    history_table = Table(title="Transaction History", show_header=True, header_style="bold magenta")
                    history_table.add_column("Type", style="cyan")
                    history_table.add_column("Amount", style="green")
                    history_table.add_column("Balance After", style="green")
                    history_table.add_column("Recipient", style="yellow")
                    history_table.add_column("Timestamp", style="white")
                    for t in history:
                        recipient_text = t.get("recipient", "-")
                        history_table.add_row(
                            t["type"],
                            f"Rp{Decimal(t['amount']):,}",
                            f"Rp{Decimal(t['balance_after']):,}",
                            recipient_text,
                            t["timestamp"]
                        )
                    console.print(history_table)
            
            elif choice == "6":
                old_pin = Prompt.ask("[bold yellow]Enter your current PIN[/bold yellow]", password=True).strip()
                new_pin = Prompt.ask("[bold yellow]Enter your new PIN[/bold yellow]", password=True).strip()
                success, message = atm.change_pin(old_pin, new_pin)
                console.print(f"[bold blue]{message}[/bold blue]")
            
            elif choice == "7":
                # Simulate a monthly interest accrual of 1%
                success, message = atm.simulate_interest(Decimal("0.01"))
                console.print(f"[bold blue]{message}[/bold blue]")
            
            elif choice == "8":
                atm.logout()
                console.print("[bold green]Logged out successfully[/bold green]")
            
            elif choice == "9":
                console.print("[bold green]Exiting... Goodbye![/bold green]")
                break
            
            else:
                console.print("[bold red]Invalid option. Please select between 1 and 9.[/bold red]")
        
        except ValueError:
            console.print("[bold red]Invalid input. Please try again.[/bold red]")
        except SecurityError as se:
            console.print(f"[bold red]Security error: {se}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
            atm.logger.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
```

---
