import sqlite3
from aiogram import Router, types, F
from aiogram.types import FSInputFile
from database import get_db_connection
from config import ADMIN_ID
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

router = Router()

@router.message(F.text == "/order_list")
async def list_orders(message: types.Message):
    """Handles /order_list command for admin to view recent orders as a PDF."""
    if message.from_user.id not in ADMIN_ID:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    orders = get_recent_orders()
    if not orders:
        await message.reply("📭 No orders found.")
        return

    # Generate PDF
    pdf_path = "orders_report.pdf"
    generate_orders_pdf(orders, pdf_path)

    # Send PDF file
    await message.answer_document(FSInputFile(pdf_path), caption="📦 Recent Orders Report")


@router.message(F.text.startswith("/see_order"))
async def order_details(message: types.Message):
    """Handles /see_order <order_id> command for admin to view order details as a PDF."""
    if message.from_user.id not in ADMIN_ID:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("⚠️ Usage: /see_order <order_id>")
        return

    try:
        order_id = int(args[1])
        order = get_order_details(order_id)
        if not order:
            await message.reply(f"⚠️ No order found with ID {order_id}.")
            return

        # Generate order PDF
        pdf_path = f"order_{order_id}.pdf"
        generate_order_pdf(order, pdf_path)

        # Send PDF file
        await message.answer_document(FSInputFile(pdf_path), caption=f"📄 Order Details (ID: {order_id})")

    except ValueError:
        await message.reply("⚠️ Invalid Order ID. Please enter a numeric value.")


def get_recent_orders():
    """Fetches recent orders from the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, employee_id, customer_fullname, status, created_at 
            FROM orders ORDER BY created_at DESC LIMIT 10
        """)
        return cursor.fetchall()


def get_order_details(order_id: int):
    """Fetches details of a specific order."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, employee_id, customer_fullname, customer_phone, product_name, product_code, 
                   quantity, wilaya, baladiya, exact_address, status, created_at
            FROM orders WHERE id = ?
        """, (order_id,))
        return cursor.fetchone()


def generate_orders_pdf(orders, pdf_path):
    """Generates a PDF report for recent orders."""
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "📦 Recent Orders Report")

    c.setFont("Helvetica", 12)
    y_position = height - 80
    for order in orders:
        order_id, employee_id, customer_name, status, created_at = order
        text = f"🆔 Order ID: {order_id} | 👤 {customer_name} | 📅 {created_at} | 🔹 {status}"
        c.drawString(50, y_position, text)
        y_position -= 20

        if y_position < 50:  # Create a new page if needed
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 50

    c.save()


def generate_order_pdf(order, pdf_path):
    """Generates a PDF file for a specific order's details."""
    order_id, employee_id, customer_fullname, customer_phone, product_name, product_code, quantity, wilaya, baladiya, exact_address, status, created_at = order

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, f"📦 Order Details (ID: {order_id})")

    c.setFont("Helvetica", 12)
    details = [
        f"🆔 Order ID: {order_id}",
        f"👤 Employee ID: {employee_id}",
        f"👤 Customer: {customer_fullname} ({customer_phone})",
        f"📦 Product: {product_name} (Code: {product_code})",
        f"📊 Quantity: {quantity}",
        f"📍 Address: {wilaya}, {baladiya}, {exact_address}",
        f"🔹 Status: {status}",
        f"📅 Date: {created_at}",
    ]

    y_position = height - 100
    for line in details:
        c.drawString(50, y_position, line)
        y_position -= 20

    c.save()
