import time
from threading import Thread

from src.decorators.background import background
from src.handlers.kcp_interface import KCPHandler
from src.logger.bot_logger import BotLogger
from src.thread_executor.executor_interface import ThreadExecutor


class ClientExecutor(ThreadExecutor):
    def __init__(self, bot_logger: BotLogger):
        super(ClientExecutor, self).__init__()
        self._bot_logger: BotLogger = bot_logger
        self._client_handlers: list[KCPHandler] = []
        self._running_handlers: dict[Thread, KCPHandler] = {}

    def add_handler(self, handler: KCPHandler):
        if handler not in self._client_handlers:
            self._client_handlers.append(handler)

    def tick(self) -> None:
        time.sleep(10)
        self._handler_checker()
        if len(self._running_handlers) >= len(self._client_handlers):
            return
        active_clients: list[KCPHandler] = list(self._running_handlers.copy().values())
        for handler in self._client_handlers:
            if handler not in active_clients:
                self._running_handlers[self._run_handler(handler)] = handler
                return

    @background("CLIENT_HANDLER")
    def _run_handler(self, handler: KCPHandler):
        try:
            handler.download_bin()
            handler.run_kcp()
        except Exception as e:
            self._bot_logger.error(str(e))

    def _handler_checker(self):
        for t in self._running_handlers.copy().keys():
            if t.is_alive():
                continue
            self._running_handlers.pop(t)
