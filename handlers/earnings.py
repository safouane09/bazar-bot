from aiogram import types, F, Router
from database import get_employee_earnings  # Function to fetch earnings

# Create a router instance
router = Router()

@router.message(F.text == "/earnings")
async def earnings(message: types.Message):
    user_id = message.from_user.id
    earnings_data = get_employee_earnings(user_id)

    if earnings_data:
        total_earnings, available_balance = earnings_data
        response = (
            "💰 *Your Earnings Overview* 💰\n\n"
            f"🔹 *Total Earnings:*  {total_earnings} DZD\n"
            f"🔹 *Available Balance:*  {available_balance} DZD\n\n"
            "📌 Minimum withdrawal: *2000 DZD*\n"
            "To request a payment, use: `/request_payment`"
        )
    else:
        response = "❌ No earnings found. Start placing orders to earn commissions!"

    await message.answer(response, parse_mode="Markdown")
