import platform

from src.handlers.kcp_interface import KCP
from src.helpers.detector import Detector, Arch, OS
from src.logger.bot_logger import BotLogger


class InvalidSystemException(Exception):
    def __init__(self, msg: str):
        super(InvalidSystemException, self).__init__(msg)


class SystemHandler(KCP):
    def __init__(self, bot_logger: BotLogger):
        super(SystemHandler, self).__init__(bot_logger)

    def _download_bin(self):
        detector: Detector = Detector()
        arch: Arch = detector.detect_arch(platform.uname().machine)
        os: OS = detector.detect_os(platform.uname().system)
        if not arch or not os:
            raise InvalidSystemException(f"Unable to find a valid os or arch, information found: os={os}, arch={arch}, information retrieved: os={platform.uname().system}, arch={platform.uname().machine}")
        print(arch, os)

    def run_kcp(self):
        pass
