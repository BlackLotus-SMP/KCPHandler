import socket
from typing import Optional

from paramiko.channel import ChannelFile
from paramiko.client import SSHClient, AutoAddPolicy

from src.config.kcp_config import KCPConfig
from src.handlers.kcp_interface import KCPHandler
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class SSHHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, config: KCPConfig, ssh_user: str, ssh_passwd: str, ssh_host: str, ssh_port: int):
        super(SSHHandler, self).__init__(bot_logger, svc_mode, config)
        self._bot_logger: BotLogger = bot_logger
        self._kcp_file: Optional[str] = None
        self._config: KCPConfig = config

        self._ssh_user: str = ssh_user
        self._ssh_pass: str = ssh_passwd
        self._ssh_port: int = ssh_port
        self._ssh_host: str = ssh_host

    def download_bin(self):
        client: SSHClient = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        client.connect(hostname=self._ssh_host, port=self._ssh_port, username=self._ssh_user, password=self._ssh_pass)
        stdin, stdout, stderr = client.exec_command("ls -lah")
        stdin.close()
        stderr.close()
        for line in iter(lambda: stdout.readline(2048), ""):
            print(line, end="")
        stdout.close()

    def run_kcp(self):
        pass
