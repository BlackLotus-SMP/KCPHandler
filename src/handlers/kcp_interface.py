from datetime import datetime
from typing import Optional

from src.config.kcp_config import KCPConfig
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class KCPHandler:
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, config: KCPConfig):
        self._bot_logger: BotLogger = bot_logger
        self._svc_mode: ServiceMode = svc_mode
        self._config: KCPConfig = config

    def download_bin(self):
        raise NotImplementedError

    def run_kcp(self):
        raise NotImplementedError

    def get_handler_type(self) -> str:
        return self.__class__.__name__

    @classmethod
    def get_unique_name(cls) -> str:
        return datetime.now().strftime("%d%m%Y%H%M%S%f")

    def is_client(self) -> bool:
        return self._svc_mode == ServiceMode.CLIENT

    def is_server(self) -> bool:
        return self._svc_mode == ServiceMode.SERVER

    def get_service_mode(self) -> ServiceMode:
        return self._svc_mode
