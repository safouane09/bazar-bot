import sqlite3

import cursor

DB_PATH = "bazarbot.db"

def get_db_connection():
    """Returns a shared database connection."""
    return sqlite3.connect(DB_PATH, timeout=10)

def create_tables():
    """Creates all necessary tables in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create employees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                invited_by INTEGER,
                balance INTEGER DEFAULT 0,
                earnings INTEGER DEFAULT 0,
                date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                invite_count INTEGER DEFAULT 0,
                FOREIGN KEY (invited_by) REFERENCES employees (id)
            )
        ''')

        # Create referrals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                referred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES employees (id),
                FOREIGN KEY (referred_id) REFERENCES employees (id),
                UNIQUE (referred_id)  -- Ensures a user can only be referred once
            )
        ''')

        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                customer_fullname TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                product_name TEXT NOT NULL,
                product_code TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                wilaya TEXT NOT NULL,
                baladiya TEXT NOT NULL,
                exact_address TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')


        # Create payement table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            employee_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT CHECK( status IN ('pending', 'approved', 'paid') ) DEFAULT 'pending',
            total_balance INTEGER NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP NULL
        )
        ''')




        print("✅ All tables created successfully!")

def add_employee(telegram_id, full_name, phone_number, referrer_id=None):
    """Adds a new employee to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ✅ Check if the user already exists
        cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (telegram_id,))
        existing_user = cursor.fetchone()
        if existing_user:
            print(f"⚠️ Employee with Telegram ID {telegram_id} already exists! No registration needed.")
            return False

        # ✅ Check if the referral ID is valid (must exist in DB)
        if referrer_id:
            cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (referrer_id,))
            referrer = cursor.fetchone()

            if not referrer:
                print(f"⚠️ Referral ID {referrer_id} is invalid. Skipping referral reward.")
                referrer_id = None
            else:
                referrer_id = referrer[0]  # Get actual employee ID

        # ✅ Register the new employee
        cursor.execute(
            "INSERT INTO employees (telegram_id, full_name, phone_number, invited_by, balance, earnings, date_joined, invite_count) VALUES (?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, 0)",
            (telegram_id, full_name, phone_number, referrer_id)
        )

        print(f"✅ Employee {telegram_id} added successfully!")

        # ✅ Handle referral tracking
        if referrer_id:
            from handlers.referral_utils import add_referral  # 🔥 FIX: Import inside function
            add_referral(referrer_id, telegram_id)

    return True

def get_employee(telegram_id):
    """Fetches an employee from the database by Telegram ID and returns it as a dictionary."""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row  # Enables dictionary-like row access
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE telegram_id = ?", (telegram_id,))
        employee = cursor.fetchone()

    return dict(employee) if employee else None  # Convert row to dictionary
def add_order(employee_telegram_id, customer_fullname, customer_phone, product_name, product_code, quantity, wilaya, baladiya, exact_address):
    """Adds an order placed by an employee."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ✅ Get employee ID from Telegram ID
        cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (employee_telegram_id,))
        employee = cursor.fetchone()

        if not employee:
            print(f"⚠️ Employee with Telegram ID {employee_telegram_id} not found!")
            return False

        employee_id = employee[0]

        # ✅ Insert order
        cursor.execute(
            "INSERT INTO orders (employee_id, customer_fullname, customer_phone, product_name, product_code, quantity, wilaya, baladiya, exact_address, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')",
            (employee_id, customer_fullname, customer_phone, product_name, product_code, quantity, wilaya, baladiya, exact_address)
        )

        print(f"✅ Order stored for Employee {employee_telegram_id}")

    return True

def get_employee_orders(employee_telegram_id):
    """Fetches all past orders placed by the employee."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get Employee ID from Telegram ID
        cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (employee_telegram_id,))
        employee = cursor.fetchone()

        if not employee:
            return []  # Employee not found

        employee_id = employee[0]

        # Fetch all orders for this employee
        cursor.execute("""
            SELECT product_name, product_code, quantity, wilaya, baladiya, status
            FROM orders
            WHERE employee_id = ?
            ORDER BY id DESC
        """, (employee_id,))

        return cursor.fetchall()  # List of orders






def get_employee_earnings(telegram_id):
    """Fetch total earnings and available balance for an employee."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Fetch total earnings (sum of commissions from orders)
            cursor.execute(
                "SELECT balance FROM employees WHERE telegram_id = ?",
                (telegram_id,)
            )
            available_balance = cursor.fetchone()[0] or 0

            # Fetch total paid earnings (approved payments)
            cursor.execute(
                "SELECT earnings FROM employees WHERE telegram_id = ?",
                (telegram_id,)
            )
            total_earnings = cursor.fetchone()[0] or 0



        return total_earnings, available_balance

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0, 0  # Return 0 earnings in case of an error





def request_payment(telegram_id,amount):
    """Request a payment if the employee has enough balance."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get employee total balance
        cursor.execute("SELECT balance FROM employees WHERE telegram_id = ?", (telegram_id,))
        total_balance = cursor.fetchone()[0] or 0  # Avoid NoneType errors

        # Get employee total balance
        cursor.execute("SELECT full_name FROM employees WHERE telegram_id = ?", (telegram_id,))
        employee_name = cursor.fetchone()[0] or 0  # Avoid NoneType errors
        # Get employee total balance
        cursor.execute("SELECT phone_number FROM employees WHERE telegram_id = ?", (telegram_id,))
        phone_number = cursor.fetchone()[0] or 0  # Avoid NoneType errors



        # Check if employee has enough balance
        if total_balance < 2000 or amount > total_balance:
            return False, total_balance  # Not enough balance

        # Insert request into payments table
        cursor.execute("""
            INSERT INTO payments (employee_id, employee_name, phone_number, amount, status, total_balance)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (telegram_id, employee_name, phone_number, amount, total_balance))

        conn.commit()

    return True, total_balance  # Request successful





# ✅ Run table creation on startup
create_tables()
