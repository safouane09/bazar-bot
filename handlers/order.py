import os
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, FSInputFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from config import ADMIN_ID  # ✅ Import admin list
from database import add_order, get_employee

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, gray
from datetime import datetime

router = Router()

# ✅ Ensure ADMIN_ID is correctly handled
admin_id = ADMIN_ID[0] if isinstance(ADMIN_ID, list) else ADMIN_ID


class OrderForm(StatesGroup):
    customer_fullname = State()
    customer_phone = State()
    product_name = State()
    product_code = State()
    quantity = State()
    wilaya = State()
    baladiya = State()
    exact_address = State()


@router.message(F.text == "/place_order")
async def start_order(message: Message, state: FSMContext):
    employee = get_employee(message.from_user.id)
    if not employee:
        await message.answer("⚠️ You are not registered! Please use /start to register first.")
        return

    await message.answer("📝 Enter the customer's full name:")
    await state.set_state(OrderForm.customer_fullname)


@router.message(OrderForm.customer_fullname)
async def get_customer_name(message: Message, state: FSMContext):
    await state.update_data(customer_fullname=message.text)
    await message.answer("📞 Enter the customer's phone number:")
    await state.set_state(OrderForm.customer_phone)


@router.message(OrderForm.customer_phone)
async def get_customer_phone(message: Message, state: FSMContext):
    await state.update_data(customer_phone=message.text)
    await message.answer("📦 Enter the product name:")
    await state.set_state(OrderForm.product_name)


@router.message(OrderForm.product_name)
async def get_product_name(message: Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await message.answer("🔢 Enter the product code:")
    await state.set_state(OrderForm.product_code)


@router.message(OrderForm.product_code)
async def get_product_code(message: Message, state: FSMContext):
    await state.update_data(product_code=message.text)
    await message.answer("🔢 Enter the quantity:")
    await state.set_state(OrderForm.quantity)


@router.message(OrderForm.quantity)
async def get_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Please enter a valid quantity (number).")
        return

    await state.update_data(quantity=int(message.text))
    await message.answer("📍 Enter the wilaya (state):")
    await state.set_state(OrderForm.wilaya)


@router.message(OrderForm.wilaya)
async def get_wilaya(message: Message, state: FSMContext):
    await state.update_data(wilaya=message.text)
    await message.answer("🏙 Enter the baladiya (city):")
    await state.set_state(OrderForm.baladiya)


@router.message(OrderForm.baladiya)
async def get_baladiya(message: Message, state: FSMContext):
    await state.update_data(baladiya=message.text)
    await message.answer("📌 Enter the exact address:")
    await state.set_state(OrderForm.exact_address)


@router.message(OrderForm.exact_address)
async def get_exact_address(message: Message, state: FSMContext):
    await state.update_data(exact_address=message.text)
    data = await state.get_data()
    employee_id = message.from_user.id
    employee = get_employee(employee_id)

    if not employee:
        await message.answer("⚠️ Employee not found. Please register first.")
        return

    # Save Order to Database
    try:
        order_id = add_order(
            employee_id,
            customer_fullname=data["customer_fullname"],
            customer_phone=data["customer_phone"],
            product_name=data["product_name"],
            product_code=data["product_code"],
            quantity=data["quantity"],
            wilaya=data["wilaya"],
            baladiya=data["baladiya"],
            exact_address=data["exact_address"]
        )
        await message.answer("✅ Order placed successfully! Status: Pending.")

        # Generate & Send PDF
        pdf_path = generate_order_pdf(order_id, data, employee)
        pdf_file = FSInputFile(pdf_path)

        # ✅ Send the order to the first admin
        await message.bot.send_document(chat_id=admin_id, document=pdf_file, caption="📄 New Order Received")

        # Cleanup
        os.remove(pdf_path)
    except Exception as e:
        await message.answer("❌ Error placing order. Please try again.")
        print(f"Error placing order: {e}")

    await state.clear()





def generate_order_pdf(order_id, data, employee):
    """Generates a visually improved PDF for the order and returns the file path."""
    pdf_path = f"order_{order_id}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)

    # Colors & Styling
    c.setFillColor(black)

    # **Header Section**
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, 820, "🛍 Bazar Order Confirmation")
    c.setFont("Helvetica", 12)
    c.setFillColor(gray)
    c.drawString(200, 800, f"Order ID: {order_id}  |  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.setFillColor(black)

    # **Employee Details**
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 770, "👨‍💼 Employee Details")
    c.setFont("Helvetica", 12)
    c.drawString(70, 750, f"🆔 ID: {employee['id']}")
    c.drawString(70, 730, f"👤 Name: {employee['full_name']}")
    c.drawString(70, 710, f"📞 Phone: {employee['phone_number']}")
    c.drawString(70, 690, f"💬 Telegram: {employee['telegram_id']}")

    # **Customer & Order Details**
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 660, "📦 Order Details")
    c.setFont("Helvetica", 12)
    c.drawString(70, 640, f"👤 Customer: {data['customer_fullname']} ({data['customer_phone']})")
    c.drawString(70, 620, f"📦 Product: {data['product_name']} (Code: {data['product_code']})")
    c.drawString(70, 600, f"🔢 Quantity: {data['quantity']}")

    # **Address Section**
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 570, "📍 Shipping Address")
    c.setFont("Helvetica", 12)
    c.drawString(70, 550, f"🏙 Wilaya: {data['wilaya']}")
    c.drawString(70, 530, f"🏠 Baladiya: {data['baladiya']}")
    c.drawString(70, 510, f"📌 Exact Address: {data['exact_address']}")

    # **Status Section**
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 480, "🔹 Order Status")
    c.setFont("Helvetica", 12)
    c.drawString(70, 460, "🟡 Pending")

    # **Footer (Signature or Notes)**
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 420, "📜 Notes:")
    c.setFont("Helvetica-Oblique", 12)
    c.drawString(70, 400, "⚠ Please confirm the order details before processing.")

    c.save()
    return pdf_path
