import os.path
import platform
import re
import shutil
import tarfile
from subprocess import PIPE, Popen, STDOUT
from typing import Optional

import requests

from src.config.kcp_config import KCPConfig
from src.constant import KCPTUN_URL
from src.handlers.handler_config_interface import HandlerConfig
from src.handlers.kcp_interface import KCPHandler, GithubDownloadException, InvalidSystemException
from src.handlers.process_interface import KCPProcess
from src.handlers.status import KCPStatus
from src.helpers.detector import Detector, Arch, OS
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class SystemProcessException(Exception):
    def __init__(self):
        super(SystemProcessException, self).__init__()


class KCPSystemProcess(KCPProcess):
    def __init__(self, bot_logger: BotLogger, is_client: bool, kcp_config: KCPConfig):
        super().__init__(bot_logger, is_client, kcp_config)
        self._process: Optional[PIPE] = None

    def start(self, kcp_path: str):
        self._start_kcp_process(kcp_path)
        self._process_status: KCPStatus = KCPStatus.RUNNING
        try:
            self._kcp_listener()
        except SystemProcessException:
            self._process_status: KCPStatus = KCPStatus.STOPPED
            self._bot_logger.warning("Process finished")
        except Exception as e:
            self._process_status: KCPStatus = KCPStatus.FAILED
            self._bot_logger.error(e)

    def _start_kcp_process(self, kcp_path: str):
        if self._is_client:
            kcp_command: str = f"{kcp_path} -r {self._kcp_config.remote} -l {self._kcp_config.listen} -mode {self._kcp_config.mode} --crypt {self._kcp_config.crypt} --key {self._kcp_config.key}"
        else:
            kcp_command: str = f"{kcp_path} -t {self._kcp_config.remote} -l {self._kcp_config.listen} -mode {self._kcp_config.mode} --crypt {self._kcp_config.crypt} --key {self._kcp_config.key}"

        self._process = Popen(kcp_command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)

    def _kcp_listener(self):
        while True:
            try:
                text: bytes = next(iter(self._process.stdout))
            except StopIteration:
                raise SystemProcessException
            else:
                _ = text
                # self._bot_logger.info(text.decode("utf8")[:-1])


class SystemHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, kcp_config: KCPConfig, handler_config: HandlerConfig):
        super(SystemHandler, self).__init__(bot_logger, svc_mode, kcp_config, handler_config)
        self._bot_logger: BotLogger = bot_logger
        self._kcp_file: Optional[str] = None
        self._kcp_config: KCPConfig = kcp_config

    def download_bin(self):
        detector: Detector = Detector()
        arch: Arch = detector.detect_arch(platform.uname().machine)
        os_: OS = detector.detect_os(platform.uname().system)
        if not arch or not os_:
            raise InvalidSystemException(f"Unable to find a valid os or arch, information found: os={os_.value}, arch={arch.value}, information retrieved: os={platform.uname().system}, arch={platform.uname().machine}")
        self._bot_logger.info(f"Found {os_.value} with {arch.value}")
        try:
            r = requests.get(KCPTUN_URL)
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
        if os.path.isdir("resources"):
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
        self._bot_logger.info(f"Found a valid binary! {self._kcp_file} ready!")

    def run_kcp(self):
        kcp_process: KCPSystemProcess = KCPSystemProcess(self._bot_logger, self.is_client(), self._kcp_config)
        kcp_process.start(self._kcp_file)
