import re
import socket
from typing import Optional

import requests
from paramiko.channel import ChannelFile
from paramiko.client import SSHClient, AutoAddPolicy

from src.config.kcp_config import KCPConfig
from src.handlers.kcp_interface import KCPHandler, InvalidSystemException, GithubDownloadException
from src.helpers.detector import Detector, Arch, OS
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class SSHHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, config: KCPConfig, ssh_user: str, ssh_pass: str, ssh_host: str, ssh_port: int):
        super(SSHHandler, self).__init__(bot_logger, svc_mode, config)
        self._bot_logger: BotLogger = bot_logger
        self._kcp_file: Optional[str] = None
        self._config: KCPConfig = config

        self._ssh_user: str = ssh_user
        self._ssh_pass: str = ssh_pass
        self._ssh_port: int = ssh_port
        self._ssh_host: str = ssh_host

        self._ssh_client: Optional[SSHClient] = None

    def _simple_command(self, command: str) -> str:
        stdin, stdout, stderr = self._ssh_client.exec_command(command)
        stdin.close()
        stderr.close()
        output: str = ""
        for line in iter(lambda: stdout.readline(2048), ""):
            output += line
        stdout.close()
        return output

    def download_bin(self):
        self._ssh_client: SSHClient = SSHClient()
        self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        self._ssh_client.connect(hostname=self._ssh_host, port=self._ssh_port, username=self._ssh_user, password=self._ssh_pass)
        detector: Detector = Detector()
        arch: Arch = detector.detect_arch(self._simple_command("uname -m"))
        os_: OS = detector.detect_os(self._simple_command("uname -s"))
        if not arch or not os_:
            raise InvalidSystemException(f"Unable to find a valid os or arch, information found: os={os_.value}, arch={arch.value}, report with your 'uname -s' and 'uname -m'")
        self._bot_logger.info(f"Found {os_.value} with {arch.value}")
        try:
            r = requests.get("https://api.github.com/repos/xtaci/kcptun/releases/latest")
        except Exception as e:
            self._bot_logger.error(f"Unable to get valid KCP assets {e}")
            raise GithubDownloadException(f"Unable to get valid KCP assets {e}")
        if r.status_code != 200:
            raise GithubDownloadException(f"Unable to get a valid release, got status code {r.status_code}!")
        data: dict = r.json()
        assets: list[dict] = data.get("assets")
        ver: str = rf"^kcptun-{os_.value}-{arch.value}-\d+.tar.gz$"
        download_url: str = ""
        for asset in assets:
            asset_name: str = asset.get("name")
            if re.search(ver, asset_name):
                download_url = asset.get("browser_download_url")
                break
        if not download_url:
            raise InvalidSystemException(f"Couldn't find a valid version for this os and arch, information found: os={os_.value}, arch={arch.value}, report with your 'uname -s' and 'uname -m'")
        self._bot_logger.info("Found a valid release!")
        self._bot_logger.info(f"Downloading {download_url}...")

    def run_kcp(self):
        pass
