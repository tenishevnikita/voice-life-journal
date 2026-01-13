"""Main bot entry point."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.handlers import router
from src.config import config


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def main() -> None:
    """Run the bot."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Voice Life Journal bot...")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Log level: {config.log_level}")

    if config.allowed_user_ids:
        logger.info(f"User whitelist enabled: {len(config.allowed_user_ids)} users allowed")
    else:
        logger.warning("User whitelist disabled - all users can access the bot")

    # Initialize bot and dispatcher
    bot = Bot(
        token=config.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Register handlers
    dp.include_router(router)

    # Start polling
    try:
        logger.info("Bot started successfully. Listening for messages...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error while running bot: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down bot...")
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
