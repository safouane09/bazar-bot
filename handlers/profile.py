from aiogram import Router, F
from aiogram.types import Message
from database import get_employee

router = Router()

# Handle /profile command
@router.message(F.text == "/profile")
async def profile_command(message: Message):
    user = get_employee(message.from_user.id)

    if not user:
        await message.answer("❌ You are not registered! Use /start to register.")
        return

    print("DEBUG: User Data ->", user)  # Debugging Output

    # Ensure user is a dictionary and has required keys
    if isinstance(user, dict) and all(key in user for key in ["full_name", "phone_number", "invited_by", "balance", "earnings", "date_joined"]):
        full_name = user.get("full_name", "❌ Not Provided")
        phone_number = user.get("phone_number", "❌ Not Provided")
        invited_by = user.get("invited_by", "❌ Not Invited")
        balance = user.get("balance", 0)
        earnings = user.get("earnings", 0)
        date_joined = user.get("date_joined", "Unknown")

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
        await message.answer("❌ Error: Your profile data is incomplete. Contact support.")
