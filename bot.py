import asyncio
import logging
import os
import json
from aiohttp import web  # ✅ Web server for Koyeb health check
from aiogram import Bot, Dispatcher
from gdrive import download_db, upload_db
from config import  GDRIVE_FOLDER_ID
from database import DB_PATH
# Download database from Google Drive
download_db(DB_PATH, GDRIVE_FOLDER_ID)

# ✅ Retrieve Google Drive credentials from environment variables
google_credentials = os.getenv("GOOGLE_CREDENTIALS")
if google_credentials:
    with open("credentials.json", "w") as f:
        f.write(google_credentials)
    print("✅ credentials.json file created successfully!")
else:
    print("❌ GOOGLE_CREDENTIALS environment variable is missing!")

# ✅ Import bot token
from config import BOT_TOKEN

# ✅ Import all handlers
from handlers import start, profile
from handlers.referrals import router as referrals_router
from handlers.order import router as order_router
from handlers.order_handlers import router as order_handlers_router
from handlers.earnings import router as earnings_router
from handlers.request_payement import router as request_payement_router
from handlers.admin import router as admin_router
from handlers.adduser import router as adduser_router
from handlers.removeuser import router as removeuser_router
from handlers.list_users import router as list_users_router
from handlers.orders import router as orders_router

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)

# ✅ Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✅ Register handlers
dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(referrals_router)
dp.include_router(order_router)
dp.include_router(order_handlers_router)
dp.include_router(earnings_router)
dp.include_router(request_payement_router)
dp.include_router(admin_router)
dp.include_router(adduser_router)
dp.include_router(removeuser_router)
dp.include_router(list_users_router)
dp.include_router(orders_router)

# ✅ Dummy Web Server for Koyeb Health Check
async def health_check(request):
    return web.Response(text="OK")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

# ✅ Main function (bot + web server)
async def main():
    logging.info("🚀 Starting bot...")
    await asyncio.gather(
        dp.start_polling(bot),
        run_web_server()
    )

# ✅ Run the bot
if __name__ == "__main__":
    asyncio.run(main())

import atexit

def on_exit():
    """Upload database when bot stops."""
    upload_db(DB_PATH, GDRIVE_FOLDER_ID)

atexit.register(on_exit)
