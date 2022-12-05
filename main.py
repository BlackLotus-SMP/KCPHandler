from src.constant import BOT_NAME
from src.handlers.system import SystemHandler
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode
from src.thread_executor.server_executor import ServerExecutor

if __name__ == '__main__':
    bot_logger = BotLogger()
    bot_logger.info(f"Started {BOT_NAME} bot")

    server = SystemHandler(bot_logger, ServiceMode.SERVER)
    server_executor: ServerExecutor = ServerExecutor(bot_logger, server)
    server_executor.start()

    server_executor.join()
