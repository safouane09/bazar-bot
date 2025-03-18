from aiogram import types, Router, F  # ✅ Correct imports

router = Router()  # ✅ Correct way to initialize the router

@router.message(F.text == "/referrals")  # ✅ Ignore commands
async def show_referrals(message: types.Message):
    from handlers.referral_utils import count_referrals  # ✅ Import inside function

    user_id = message.from_user.id
    referral_count, earnings = count_referrals(user_id)

    await message.answer(f"📊 You have referred {referral_count} users.\n💰 Total earnings: {earnings} DZD")
