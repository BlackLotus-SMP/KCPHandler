import time
from threading import Thread
from typing import Optional

from src.decorators.background import background
from src.handlers.kcp_interface import KCPHandler
from src.logger.bot_logger import BotLogger
from src.thread_executor.executor_interface import ThreadExecutor


class ServerExecutor(ThreadExecutor):
    def __init__(self, bot_logger: BotLogger, kcp_handler: KCPHandler):
        super(ServerExecutor, self).__init__()
        self._bot_logger: BotLogger = bot_logger
        self._kcp_handler: KCPHandler = kcp_handler
        self._kcp_handler_thread: Optional[Thread] = None

    @background("SERVER_HANDLER")
    def _run_server(self):
        try:
            self._kcp_handler.download_bin()
            self._kcp_handler.run_kcp()
        except Exception as e:
            self._bot_logger.error(e)
        self._bot_logger.warning("Process finished! retrying in 30 seconds")
        time.sleep(30)
        self._kcp_handler_thread: Optional[Thread] = None

    def tick(self) -> None:
        if not self._kcp_handler_thread or not self._kcp_handler_thread.is_alive():
            self._kcp_handler_thread: Optional[Thread] = self._run_server()

        time.sleep(10)
