import sqlite3
from aiogram import Router, types, F
from aiogram.types import FSInputFile
from fpdf import FPDF
import os

from database import get_db_connection
from config import ADMIN_ID

router = Router()

@router.message(F.text == "/list_users")
async def list_users_command(message: types.Message):
    """Handles /list_users command for admin to generate a PDF report of all employees."""
    if message.from_user.id not in ADMIN_ID:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    employees = get_all_employees()

    if not employees:
        await message.reply("ℹ️ No employees found.")
        return

    pdf_path = generate_pdf(employees)

    # Send the PDF file
    pdf_file = FSInputFile(pdf_path)
    await message.reply_document(pdf_file, caption="📄 Employee List Report")

    # Delete the PDF after sending
    os.remove(pdf_path)

def get_all_employees():
    """Fetches all employees from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, telegram_id, full_name, phone_number, invited_by, balance, earnings, date_joined, invite_count 
                FROM employees
            """)
            return cursor.fetchall()
    except sqlite3.Error:
        return []

def generate_pdf(employees):
    """Generates a PDF file with employee details in a table format."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")  # Landscape mode for better spacing
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(280, 10, "Employee List Report", ln=True, align="C")
    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", "B", 9)
    headers = ["ID", "Telegram ID", "Full Name", "Phone", "Invited By", "Balance", "Earnings", "Date Joined", "Invites"]
    col_widths = [10, 30, 50, 25, 30, 25, 25, 35, 15]  # Adjusted column widths

    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, "C")
    pdf.ln()

    # Table Rows
    pdf.set_font("Arial", "", 9)
    for emp in employees:
        for i, data in enumerate(emp):
            pdf.cell(col_widths[i], 10, str(data), 1, 0, "C")
        pdf.ln()

    # Save PDF file
    pdf_filename = "employee_list.pdf"
    pdf.output(pdf_filename)
    return pdf_filename
