from aiogram import Router, types, F

from config import ADMIN_ID

router = Router()

@router.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_ID:
        await message.answer("🚫 You are not authorized to access the admin panel.")
        return

    response = (
        "🔹 *Admin Panel*\n\n"
        "✅ /add_employee <telegram_id> <name> <phone>\n"
        "❌ /remove_employee <telegram_id>\n"
        "📦 /orders → View orders\n"
        "📝 /update_order <order_id> <status>\n"
        "💰 /commissions → View commissions\n"
    )
    await message.answer(response, parse_mode="Markdown")



