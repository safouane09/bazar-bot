import sqlite3
from aiogram import Router, types, F

from database import get_db_connection
from config import ADMIN_ID

router = Router()

@router.message(F.text.startswith("/remove_user"))
async def remove_user_command(message: types.Message):
    """Handles /remove_user command for admin to remove an employee."""
    if message.from_user.id not in ADMIN_ID:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Usage: /remove_user <telegram_id>")
        return

    try:
        telegram_id = int(args[1])

        if remove_employee(telegram_id):
            await message.reply(f"✅ Employee with Telegram ID {telegram_id} removed successfully!")
        else:
            await message.reply(f"⚠️ No employee found with Telegram ID {telegram_id}.")
    except ValueError:
        await message.reply("⚠️ Invalid Telegram ID. Please enter a numeric value.")

def remove_employee(telegram_id: int) -> bool:
    """Removes an employee from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees WHERE telegram_id = ?", (telegram_id,))
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False
    except sqlite3.Error:
        return False
