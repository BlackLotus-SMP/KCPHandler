from src.kcp.kcp_config import KCPConfig
from src.logger.bot_logger import BotLogger


class KCPProcess:
    def __init__(self, bot_logger: BotLogger, is_client: bool, kcp_config: KCPConfig):
        self._bot_logger: BotLogger = bot_logger
        self._is_client: bool = is_client
        self._kcp_config: KCPConfig = kcp_config

    def start(self, kcp_path: str):
        raise NotImplementedError
