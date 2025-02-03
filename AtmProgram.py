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
    timestamp: datetime
    type: str
    amount: Decimal
    balance_after: Decimal
    recipient: Optional[str] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["amount"] = str(self.amount)
        data["balance_after"] = str(self.balance_after)
        return data


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class ATMSystem:
    def __init__(self, initial_data: list = None):
        """Initialize ATM system with user data and setup logging"""
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
        """Configure logging system with a rotating file handler"""
        self.logger = logging.getLogger("ATMSystem")
        self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler("atm_transactions.log", maxBytes=5 * 1024 * 1024, backupCount=3)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def _load_initial_data(self, initial_data: list = None):
        """Load initial user data or create default data"""
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
        """Hash password using SHA-256"""
        return hashlib.sha256(password.strip().encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user with retry limits and cooling period"""
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
        """Handle failed login attempts"""
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
        if not self.session_active or self.current_user is None:
            raise SecurityError("No active session")

    def check_balance(self) -> Decimal:
        """Check account balance"""
        self._assert_session()
        return self.accounts[self.current_user]['saldo']

    def _update_daily_total(self, trans_type: str, amount: Decimal):
        """Update the cached daily total for the current user and transaction type"""
        today = date.today()
        user_totals = self.daily_totals[self.current_user][trans_type]
        user_totals[today] = user_totals.get(today, Decimal('0')) + amount

    def _get_daily_total(self, trans_type: str) -> Decimal:
        """Retrieve the daily total for the current user and transaction type"""
        today = date.today()
        return self.daily_totals[self.current_user][trans_type].get(today, Decimal('0'))

    def _log_transaction(self, trans: Transaction):
        """Log transaction details and store it in history"""
        if self.current_user not in self.transaction_history:
            self.transaction_history[self.current_user] = []
        self.transaction_history[self.current_user].append(trans)
        self.logger.info(f"Transaction: {self.current_user} - {json.dumps(trans.to_dict())}")

    def withdraw(self, amount: Decimal) -> Tuple[bool, str]:
        """Process withdrawal with validation and limits"""
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
        """Process deposit with validation"""
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
        """Process transfer between accounts"""
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
        """Allow the current user to change their PIN"""
        self._assert_session()
        if self._hash_password(old_pin) != self.accounts[self.current_user]['password_hash']:
            return False, "Incorrect old PIN"
        self.accounts[self.current_user]['password_hash'] = self._hash_password(new_pin)
        self.logger.info(f"User {self.current_user} changed PIN.")
        return True, "PIN successfully changed."

    def simulate_interest(self, interest_rate: Decimal = Decimal("0.01")) -> Tuple[bool, str]:
        """Simulate monthly interest accrual on the account balance"""
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
        """Get transaction history for current user as list of dictionaries"""
        self._assert_session()
        return [trans.to_dict() for trans in self.transaction_history.get(self.current_user, [])]

    def logout(self):
        """End user session"""
        if self.session_active:
            self.logger.info(f"User logged out: {self.current_user}")
            self.session_active = False
            self.current_user = None


def main():
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
