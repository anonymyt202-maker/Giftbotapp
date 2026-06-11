"""
run.py — Bot va API ni bir vaqtda ishlatish
"""
import asyncio
import uvicorn
from bot.main import main as run_bot
from config import settings


async def run_api():
    config = uvicorn.Config("api.main:app", host="0.0.0.0", port=settings.PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(run_bot(), run_api())


if __name__ == "__main__":
    asyncio.run(main())
