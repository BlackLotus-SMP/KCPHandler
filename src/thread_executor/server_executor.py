import time

from src.handlers.kcp_interface import KCPHandler
from src.logger.bot_logger import BotLogger
from src.thread_executor.executor_interface import ThreadExecutor


class ServerExecutor(ThreadExecutor):
    def __init__(self, bot_logger: BotLogger, kcp_handler: KCPHandler):
        super(ServerExecutor, self).__init__()
        self._bot_logger: BotLogger = bot_logger
        self._kcp_handler: KCPHandler = kcp_handler

    def tick(self) -> None:
        # TODO retry timeout
        try:
            self._kcp_handler.download_bin()
            self._kcp_handler.run_kcp()
        except Exception as e:
            print(e)
            self._bot_logger.error(e)
        self._bot_logger.warning("Process finished! retrying in 30 seconds")
        time.sleep(30)
