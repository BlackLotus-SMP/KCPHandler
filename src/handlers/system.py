import os.path
import platform
import re
import shutil
import tarfile
from typing import Optional

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
        self._kcp_file: Optional[str] = None

    def download_bin(self):
        detector: Detector = Detector()
        arch: Arch = detector.detect_arch(platform.uname().machine)
        os_: OS = detector.detect_os(platform.uname().system)
        if not arch or not os_:
            raise InvalidSystemException(f"Unable to find a valid os or arch, information found: os={os_.value}, arch={arch.value}, information retrieved: os={platform.uname().system}, arch={platform.uname().machine}")
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
            raise InvalidSystemException(f"Couldn't find a valid version for this os and arch, information found: os={os_.value}, arch={arch.value}, information retrieved: os={platform.uname().system}, arch={platform.uname().machine}, please report!")
        self._bot_logger.info("Found a valid release!")
        self._bot_logger.info(f"Downloading {download_url}...")
        shutil.rmtree("resources")
        if not os.path.isdir("resources"):
            os.mkdir("resources")
        kcp_compressed = requests.get(download_url, stream=True)
        with open("resources/compressed.tar.gz", "wb") as f:
            for chunk in kcp_compressed.iter_content(chunk_size=2048):
                if chunk:
                    f.write(chunk)
        self._bot_logger.info(f"File downloaded")
        file: tarfile.TarFile = tarfile.open("resources/compressed.tar.gz")
        file.extractall(path="resources")
        file.close()
        os.remove("resources/compressed.tar.gz")
        self._bot_logger.info(f"Extracting a valid binary")
        files: list[str] = os.listdir("resources")
        expected_binary_format: str = "client" if self.is_client() else "server"
        expected_binary_format += f"_{os_.value}_{arch.value}"
        for bin_file in files:
            if bin_file.startswith(expected_binary_format):
                self._kcp_file = f"resources/{bin_file}"
            else:
                os.remove(f"resources/{bin_file}")
        if not self._kcp_file:
            raise InvalidSystemException(f"Couldn't find a valid executable! information found: os={os_.value}, arch={arch.value}, information retrieved: os={platform.uname().system}, arch={platform.uname().machine}, files found: {', '.join(files)}, please report")
        self._bot_logger.info(f"Found a valid binary! {self.get_binary_path()} ready!")

    def get_binary_path(self) -> Optional[str]:
        return self._kcp_file

    def run_kcp(self):
        pass
