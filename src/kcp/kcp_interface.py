from datetime import datetime

from src.kcp.kcp_config import KCPConfig
from src.handlers.handler_config import HandlerConfig
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class GithubDownloadException(Exception):
    def __init__(self, msg: str):
        super(GithubDownloadException, self).__init__(msg)


class InvalidSystemException(Exception):
    def __init__(self, msg: str):
        super(InvalidSystemException, self).__init__(msg)


class HandlerConfigNotValid(Exception):
    def __init__(self, msg: str):
        super(HandlerConfigNotValid, self).__init__(msg)


class KCPHandler:
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, kcp_config: KCPConfig, handler_config: HandlerConfig):
        self._bot_logger: BotLogger = bot_logger
        self._svc_mode: ServiceMode = svc_mode
        self._kcp_config: KCPConfig = kcp_config
        self.__handler_config: HandlerConfig = handler_config
        self._bot_logger.info(f"Starting a {self._svc_mode.value} with {self.__class__.__name__}")

    def download_bin(self):
        raise NotImplementedError

    def run_kcp(self):
        raise NotImplementedError

    @classmethod
    def get_unique_name(cls) -> str:
        return datetime.now().strftime("%d%m%Y%H%M%S%f")

    def is_client(self) -> bool:
        return self._svc_mode == ServiceMode.CLIENT

    def is_server(self) -> bool:
        return self._svc_mode == ServiceMode.SERVER

    def get_service_mode(self) -> ServiceMode:
        return self._svc_mode
