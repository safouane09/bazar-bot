import sqlite3

def count_referrals(user_id: int):
    """Counts the number of referrals and calculates earnings."""
    from database import DB_PATH  # ✅ Import inside function to prevent circular import

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get the number of referrals
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
    result = cursor.fetchone()
    referral_count = result[0] if result else 0

    # Get earnings
    cursor.execute("SELECT earnings FROM employees WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    earnings = result[0] if result else 0

    conn.close()
    return referral_count, earnings

def add_referral(referrer_id: int, referred_id: int):
    """Adds a referral and updates earnings only if the referral is new."""
    from database import get_db_connection  # ✅ Import inside function

    conn = get_db_connection()  # ✅ Use shared connection
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))

        if cursor.rowcount == 0:
            print(f"⚠️ Referral already exists: {referred_id} was referred before. Skipping earnings update.")
            return

        cursor.execute("UPDATE employees SET balance = balance + 50, earnings = earnings + 50, invite_count = invite_count + 1 WHERE telegram_id = ?", (referrer_id,))
        conn.commit()

        print(f"✅ Referrer {referrer_id} earned 50 DZD!")
        print(f"✅ Referral Added: {referrer_id} referred {referred_id}")

    except sqlite3.OperationalError as e:
        print(f"❌ Database Error: {e}")

    finally:
        cursor.close()  # ✅ Close cursor only (don't close connection)
