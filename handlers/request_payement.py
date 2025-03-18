from aiogram import types, F, Router
import sqlite3

from database import request_payment

router = Router()


@router.message(F.text == "/pay_me")
async def handle_request_payment(message: types.Message):
    telegram_id = message.from_user.id

    request_status, total_balance = request_payment(telegram_id,  2000)  # Default request 2000 DZD

    if request_status:
        response = (
            "✅ *Payment Request Submitted!*\n\n"
            f"📌 Amount: *2000 DZD*\n"
            f"💰 Your Balance: *{total_balance} DZD*\n"
            "🔄 Status: *Pending approval*\n\n"
            "🔔 *Admin will review your request soon.*"
        )
    else:
        response = (
            "❌ *Insufficient Balance!*\n\n"
            f"💰 Your Balance: *{total_balance} DZD*\n"
            "⚠️ You need at least *2000 DZD* to request a payment."
        )

    await message.answer(response, parse_mode="Markdown")
