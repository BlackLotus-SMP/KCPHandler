from src.constant import BOT_NAME
from src.handlers.linux import LinuxHandler
from src.logger.bot_logger import BotLogger

if __name__ == '__main__':
    bot_logger = BotLogger()
    bot_logger.info(f"Started {BOT_NAME} bot")

    server = LinuxHandler(bot_logger)
