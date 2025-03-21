import sqlite3
import os
import logging
from config import GDRIVE_FOLDER_ID

DB_PATH = "bazarbot.db"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def on_database_update():
    """Uploads the database after modification."""
    logging.info("🔄 Database changed! Uploading to Google Drive...")

    from gdrive import upload_db  # Import here to avoid circular dependency

    try:
        upload_db(DB_PATH, GDRIVE_FOLDER_ID)
        logging.info("✅ Database uploaded successfully!")
    except Exception as e:
        logging.error(f"❌ Failed to upload database: {e}")


def get_db_connection():
    """Returns a database connection with foreign key support."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logging.error(f"❌ Database connection error: {e}")
        return None


def create_tables():
    """Creates necessary tables."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.executescript('''
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
            );
        ''')
        conn.commit()
        logging.info("✅ Database tables created successfully!")
    except sqlite3.Error as e:
        logging.error(f"❌ Error creating tables: {e}")
    finally:
        conn.close()


def modify_db(query, params=()):
    """Executes a database modification and triggers backup."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        on_database_update()  # 🔄 Auto-upload after modification
    except sqlite3.Error as e:
        logging.error(f"❌ Database modification error: {e}")
    finally:
        conn.close()


# ✅ Run table creation on startup
create_tables()





# ✅ Employee Functions
def add_employee(telegram_id, full_name, phone_number, referrer_id=None):
    """Adds a new employee to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (telegram_id,))
        if cursor.fetchone():
            logging.warning(f"⚠️ Employee with Telegram ID {telegram_id} already exists!")
            return False

        if referrer_id:
            cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (referrer_id,))
            referrer = cursor.fetchone()
            if not referrer:
                logging.warning(f"⚠️ Invalid referral ID {referrer_id}. Skipping referral reward.")
                referrer_id = None
            else:
                referrer_id = referrer[0]

        modify_db(
            "INSERT INTO employees (telegram_id, full_name, phone_number, invited_by) VALUES (?, ?, ?, ?)",
            (telegram_id, full_name, phone_number, referrer_id)
        )
        logging.info(f"✅ Employee {telegram_id} added successfully!")

        if referrer_id:
            from handlers.referral_utils import add_referral
            add_referral(referrer_id, telegram_id)

    return True


def get_employee(telegram_id):
    """Fetches an employee from the database by Telegram ID."""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE telegram_id = ?", (telegram_id,))
        employee = cursor.fetchone()
        return dict(employee) if employee else None


# ✅ Orders Functions
def add_order(employee_telegram_id, customer_fullname, customer_phone, product_name, product_code, quantity, wilaya, baladiya, exact_address):
    """Adds an order placed by an employee."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (employee_telegram_id,))
        employee = cursor.fetchone()
        if not employee:
            logging.warning(f"⚠️ Employee with Telegram ID {employee_telegram_id} not found!")
            return False

        employee_id = employee[0]

        modify_db(
            "INSERT INTO orders (employee_id, customer_fullname, customer_phone, product_name, product_code, quantity, wilaya, baladiya, exact_address, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')",
            (employee_id, customer_fullname, customer_phone, product_name, product_code, quantity, wilaya, baladiya, exact_address)
        )
        logging.info(f"✅ Order stored for Employee {employee_telegram_id}")

    return True


def get_employee_orders(employee_telegram_id):
    """Fetches all orders placed by an employee."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM employees WHERE telegram_id = ?", (employee_telegram_id,))
        employee = cursor.fetchone()
        if not employee:
            return []

        cursor.execute("SELECT product_name, product_code, quantity, wilaya, baladiya, status FROM orders WHERE employee_id = ? ORDER BY id DESC", (employee[0],))
        return cursor.fetchall()


# ✅ Earnings Functions
def get_employee_earnings(telegram_id):
    """Fetch total earnings and available balance for an employee."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance, earnings FROM employees WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            return result if result else (0, 0)
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return 0, 0


# ✅ Payment Requests
def request_payment(telegram_id, amount):
    """Request a payment if the employee has enough balance."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT balance, full_name, phone_number FROM employees WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result:
            return False, 0

        balance, full_name, phone_number = result
        if balance < 2000 or amount > balance:
            return False, balance

        modify_db(
            "INSERT INTO payments (employee_id, employee_name, phone_number, amount, status, total_balance) VALUES (?, ?, ?, ?, 'pending', ?)",
            (telegram_id, full_name, phone_number, amount, balance)
        )
        return True, balance


# ✅ Run table creation on startup
create_tables()
