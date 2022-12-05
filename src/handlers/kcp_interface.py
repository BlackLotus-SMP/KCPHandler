from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class KCPHandler:
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode):
        self._bot_logger: BotLogger = bot_logger
        self._svc_mode: ServiceMode = svc_mode
        self._download_bin()

    def _download_bin(self):
        raise NotImplementedError

    def run_kcp(self):
        raise NotImplementedError

    def is_client(self) -> bool:
        return self._svc_mode == ServiceMode.CLIENT

    def is_server(self) -> bool:
        return self._svc_mode == ServiceMode.SERVER

    def get_service_mode(self) -> ServiceMode:
        return self._svc_mode
