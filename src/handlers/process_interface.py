from src.config.kcp_config import KCPConfig
from src.handlers.status import KCPStatus
from src.logger.bot_logger import BotLogger


class KCPProcess:
    def __init__(self, bot_logger: BotLogger, is_client: bool, kcp_config: KCPConfig):
        self._bot_logger: BotLogger = bot_logger
        self._process_status: KCPStatus = KCPStatus.STARTING
        self._is_client: bool = is_client
        self._kcp_config: KCPConfig = kcp_config
        self._bot_logger.info(f"{self.__class__.__name__} starting...")

    def start(self, kcp_path: str):
        raise NotImplementedError
