import re
from enum import Enum


class Arch(Enum):
    ARMV5 = "armv5"
    ARMV6 = "armv6"
    ARMV7 = "armv7"
    ARM64 = "arm64"
    A386 = "386"
    AMD64 = "amd64"


class OS(Enum):
    WINDOWS = "windows"
    MACOS = "darwin"
    FREEBSD = "freebsd"
    LINUX = "linux"


class Detector:
    def __init__(self):
        self._arch_detector = (
            (["armv5.*"], Arch.ARMV5),
            (["armv6.*"], Arch.ARMV6),
            (["armv7.*"], Arch.ARMV7),
            (["aarch64"], Arch.ARM64),
            (["x86", "i686", "i386"], Arch.A386),
            (["x86_64"], Arch.AMD64)
        )
        self._os_detector = (
            (["msys.*", "mingw.*"], OS.WINDOWS),
            (["darwin"], OS.MACOS),
            (["freebsd"], OS.FREEBSD),
            (["linux"], OS.LINUX)
        )

    def detect_arch(self, arch: str) -> None | Arch:
        arch_: str = arch.lower()
        for k, arch_detected in self._arch_detector:
            for key in k:
                if re.search(f"^{key}$", arch_):
                    return arch_detected
        return None

    def detect_os(self, os: str) -> None | OS:
        os_: str = os.lower()
        for k, os_detected in self._os_detector:
            for key in k:
                if re.search(f"^{key}$", os_):
                    return os_detected
        return None
