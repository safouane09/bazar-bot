from aiogram import Router, F
from aiogram.types import Message
from database import get_employee

router = Router()

# Handle /profile command
@router.message(F.text == "/profile")
async def profile_command(message: Message):
    user = get_employee(message.from_user.id)

    if user:
        full_name = user[2]  # Assuming index 2 is Full Name
        phone_number = user[3]  # Phone Number
        invited_by = user[4] if user[4] else "❌ Not Invited"  # Invited By
        balance = user[5] if user[5] else 0  # Balance
        earnings = user[6] if user[6] else 0  # Earnings
        date_joined = user[7]  # Date Joined

        profile_text = (
            f"📋 *Your Profile*\n"
            f"👤 *Name:* {full_name}\n"
            f"📞 *Phone:* {phone_number}\n"
            f"📢 *Invited By:* {invited_by}\n"
            f"💰 *Balance:* {balance} DZD\n"
            f"💵 *Total Earnings:* {earnings} DZD\n"
            f"📅 *Joined On:* {date_joined}\n"
        )

        await message.answer(profile_text, parse_mode="Markdown")
    else:
        await message.answer("❌ You are not registered! Use /start to register.")
