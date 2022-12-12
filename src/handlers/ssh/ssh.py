from typing import Optional

from src.config.kcp_config import KCPConfig
from src.handlers.kcp_interface import KCPHandler
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class SSHHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, config: KCPConfig, ssh_user: str, ssh_passwd: str):
        super(SSHHandler, self).__init__(bot_logger, svc_mode, config)
        self._bot_logger: BotLogger = bot_logger
        self._kcp_file: Optional[str] = None
        self._config: KCPConfig = config

    def download_bin(self):
        pass

    def run_kcp(self):
        pass
