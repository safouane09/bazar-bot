from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from fpdf import FPDF
import os

from database import get_employee_orders, get_employee

router = Router()

class OrderPDF(FPDF):
    def header(self):
        """Custom header with logo and title"""
        logo_path = "bazar1.jpg"  # Ensure this file exists

        # Add logo if available
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=5, w=50)  # x=10 (left), y=5 (higher), w=50 (bigger)
        # Adjust size & position

        # Title
        self.set_font("Arial", "B", 18)
        self.cell(200, 10, "Order History", ln=True, align="C")
        self.ln(15)  # Space after title

    def footer(self):
        """Custom footer with a message"""
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, "Thank you for using BazarBot!", align="C")

def generate_orders_pdf(employee_telegram_id, orders):
    pdf = OrderPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Table Header
    pdf.set_fill_color(50, 50, 50)  # Dark Gray
    pdf.set_text_color(255, 255, 255)  # White
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Product", 1, 0, "C", 1)
    pdf.cell(30, 10, "Code", 1, 0, "C", 1)
    pdf.cell(20, 10, "Qty", 1, 0, "C", 1)
    pdf.cell(40, 10, "Location", 1, 0, "C", 1)
    pdf.cell(40, 10, "Status", 1, 1, "C", 1)

    # Reset text color
    pdf.set_text_color(0, 0, 0)

    # Table Data
    pdf.set_font("Arial", size=11)
    for product_name, product_code, quantity, wilaya, baladiya, status in orders:
        pdf.cell(40, 10, product_name, 1)
        pdf.cell(30, 10, product_code, 1)
        pdf.cell(20, 10, str(quantity), 1, 0, "C")
        pdf.cell(40, 10, f"{wilaya}, {baladiya}", 1)
        pdf.cell(40, 10, status, 1, 1, "C")

    # Save the file
    filename = f"orders_{employee_telegram_id}.pdf"
    pdf.output(filename, "F")  # "F" ensures file mode write
    return filename

@router.message(F.text == "/orders")
async def show_orders(message: Message):
    print(f"DEBUG: /orders triggered by {message.from_user.id}")

    employee = get_employee(message.from_user.id)
    if not employee:
        await message.answer("⚠️ You are not registered! Please use /start to register first.")
        return

    orders = get_employee_orders(message.from_user.id)
    if not orders:
        await message.answer("📭 No orders found in your history.")
        return

    pdf_filename = None  # Fix: Declare pdf_filename before try

    try:
        # ✅ Generate PDF
        pdf_filename = generate_orders_pdf(message.from_user.id, orders)

        # ✅ Send PDF to employee
        await message.answer_document(FSInputFile(pdf_filename))

    except Exception as e:
        print(f"ERROR: Failed to send PDF - {e}")
        await message.answer("❌ An error occurred while generating your order history.")

    finally:
        # ✅ Cleanup: Remove the file after sending
        if pdf_filename and os.path.exists(pdf_filename):
            os.remove(pdf_filename)
