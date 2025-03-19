import asyncio
import logging
import threading
from aiogram import Bot, Dispatcher
from aiohttp import web  # ✅ Import web server

from config import BOT_TOKEN
from handlers import start, profile
from handlers.referrals import router as referrals_router
from handlers.order import router as order_router  # ✅ Import order router
from handlers.order_handlers import router as order_handlers_router
from handlers.earnings import router as earnings_router
from handlers.request_payement import router as request_payement_router
from handlers.admin import router as admin_router
from handlers.adduser import router as adduser_router
from handlers.removeuser import router as removeuser_router
from handlers.list_users import router as list_users_router
from handlers.orders import router as orders_router

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Register handlers
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

async def main():
    logging.info("Starting bot...")

    # ✅ Run bot and web server together
    await asyncio.gather(
        dp.start_polling(bot),
        run_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
#hna modifyiiit