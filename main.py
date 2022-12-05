from src.constant import BOT_NAME
from src.handlers.system import SystemHandler
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode

if __name__ == '__main__':
    bot_logger = BotLogger()
    bot_logger.info(f"Started {BOT_NAME} bot")

    server = SystemHandler(bot_logger, ServiceMode.SERVER)
