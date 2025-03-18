import sqlite3
from aiogram import Router, types, F
from aiogram.filters import Command
from database import get_db_connection
from config import ADMIN_ID

router = Router()

@router.message(Command("add_user"))
async def add_user_command(message: types.Message):
    """Handles /add_user command for admin to add a new employee."""

    print(f"🔍 User ID: {message.from_user.id} | Admin List: {ADMIN_ID}")  # Debug

    if message.from_user.id not in ADMIN_ID:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.reply("⚠️ Usage: /add_user <telegram_id> <full_name> <phone_number>")
        return

    try:
        telegram_id = int(args[1])
        full_name = args[2]
        phone_number = args[3]

        if add_employee(telegram_id, full_name, phone_number):
            await message.reply(f"✅ Employee {full_name} (ID: {telegram_id}) added successfully!")
        else:
            await message.reply(f"⚠️ Employee with Telegram ID {telegram_id} already exists!")
    except ValueError:
        await message.reply("⚠️ Invalid Telegram ID. Please enter a numeric value.")

def add_employee(telegram_id: int, full_name: str, phone_number: str) -> bool:
    """Adds an employee to the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO employees (telegram_id, full_name, phone_number) VALUES (?, ?, ?)",
                (telegram_id, full_name, phone_number),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
