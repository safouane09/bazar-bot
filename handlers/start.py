from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import add_employee, get_employee
from handlers.referral_utils import add_referral

router = Router()

class Register(StatesGroup):
    full_name = State()
    phone_number = State()
    referral_code = State()

request_phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📞 Send Phone Number", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

@router.message(F.text == "/start")
async def start_command(message: Message, state: FSMContext):
    user = get_employee(message.from_user.id)

    if user:
        await message.answer(f"✅ You are already registered, {user[2]}!\nUse /profile to see your info.")
    else:
        await message.answer("👋 Welcome! Please send your full name to register.")
        await state.set_state(Register.full_name)

@router.message(Register.full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("📞 Now, please send your phone number or share your contact.", reply_markup=request_phone_kb)
    await state.set_state(Register.phone_number)

@router.message(Register.phone_number)
async def get_phone_number(message: Message, state: FSMContext):
    """Handles both text and contact phone numbers."""
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text.strip()

    # ✅ More flexible phone validation (allows +213 and 213)
    if not phone_number.startswith("+213") and not phone_number.startswith("213"):
        await message.answer("⚠️ Invalid phone number! Please send a valid number (starting with +213 or 213).")
        return

    await state.update_data(phone_number=phone_number)
    print(f"✅ Phone Number Saved: {phone_number}")  # Debugging Log

    await message.answer("🔢 Enter the referral code (Telegram ID of the inviter) or type '0' if you don’t have one:")
    await state.set_state(Register.referral_code)

@router.message(Register.referral_code)
async def get_referral_code(message: Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = user_data.get("full_name")
    phone_number = user_data.get("phone_number")
    telegram_id = message.from_user.id

    referral_code = message.text.strip()
    referrer_id = int(referral_code) if referral_code.isdigit() and referral_code != "0" else None

    # ✅ Only check referrer in DB if it's valid
    if referrer_id:
        if not get_employee(referrer_id):
            await message.answer("⚠️ Invalid referral code! Please enter a valid Telegram ID or type '0' if you don’t have one:")
            return

    print(f"✅ Adding Employee: {telegram_id}, Name: {full_name}, Phone: {phone_number}, Invited By: {referrer_id}")

    add_employee(telegram_id, full_name, phone_number, referrer_id)
    print("✅ Employee Added to DB!")

    # ✅ Check if referral exists before adding to avoid duplicates
    if referrer_id:
        try:
            add_referral(referrer_id, telegram_id)
            print(f"✅ Referral Added: {referrer_id} referred {telegram_id}")
        except Exception as e:
            print(f"⚠️ Referral NOT added (maybe already exists?): {e}")

    await message.answer("✅ Registration complete!")
    await state.clear()
