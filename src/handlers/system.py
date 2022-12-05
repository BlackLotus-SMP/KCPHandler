import platform
import re

import requests

from src.handlers.kcp_interface import KCPHandler
from src.helpers.detector import Detector, Arch, OS
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class InvalidSystemException(Exception):
    def __init__(self, msg: str):
        super(InvalidSystemException, self).__init__(msg)


class GithubDownloadException(Exception):
    def __init__(self, msg: str):
        super(GithubDownloadException, self).__init__(msg)


class SystemHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode):
        super(SystemHandler, self).__init__(bot_logger, svc_mode)
        self._bot_logger: BotLogger = bot_logger

    def _download_bin(self):
        detector: Detector = Detector()
        arch: Arch = detector.detect_arch(platform.uname().machine)
        os: OS = detector.detect_os(platform.uname().system)
        if not arch or not os:
            raise InvalidSystemException(f"Unable to find a valid os or arch, information found: os={os}, arch={arch}, information retrieved: os={platform.uname().system}, arch={platform.uname().machine}")
        self._bot_logger.info(f"Found {os.value} with {arch.value}")
        try:
            r = requests.get("https://api.github.com/repos/xtaci/kcptun/releases/latest")
        except Exception as e:
            self._bot_logger.error(f"Unable to get valid KCP assets {e}")
            raise GithubDownloadException(f"Unable to get valid KCP assets {e}")
        if r.status_code != 200:
            raise GithubDownloadException(f"Unable to get a valid release, got status code {r.status_code}!")
        data: dict = r.json()
        assets: list[dict] = data.get("assets")
        ver: str = rf"^kcptun-{os.value}-{arch.value}-\d+.tar.gz$"
        download_url: str = ""
        for asset in assets:
            asset_name: str = asset.get("name")
            if re.search(ver, asset_name):
                download_url = asset.get("browser_download_url")
                break
        if not download_url:
            raise InvalidSystemException(f"Couldn't find a valid version for this os and arch, information found: os={os}, arch={arch}, information retrieved: os={platform.uname().system}, arch={platform.uname().machine}, please report!")
        self._bot_logger.info("Found a valid release!")
        self._bot_logger.info(f"Downloading {download_url}...")

    def run_kcp(self):
        pass
