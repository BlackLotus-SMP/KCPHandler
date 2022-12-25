import unittest

from src.helpers.detector import Detector, Arch, OS


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.detector: Detector = Detector()

    def test_0_arch(self):
        self.assertEqual(self.detector.detect_arch("armv5idk"), Arch.ARMV5)
        self.assertIsNone(self.detector.detect_arch("idkarmv5"), Arch.ARMV5)
        self.assertEqual(self.detector.detect_arch("ArMv7"), Arch.ARMV7)
        self.assertEqual(self.detector.detect_arch("i386"), Arch.A386)
        self.assertEqual(self.detector.detect_arch("x86"), Arch.A386)
        self.assertEqual(self.detector.detect_arch("x86_64"), Arch.AMD64)
        self.assertIsNone(self.detector.detect_arch("idk"))

    def test_1_os(self):
        self.assertEqual(self.detector.detect_os("msysidk"), OS.WINDOWS)
        self.assertIsNone(self.detector.detect_os("idkmsys"))
        self.assertEqual(self.detector.detect_os("lInUx"), OS.LINUX)
        self.assertEqual(self.detector.detect_os("freebsd"), OS.FREEBSD)
        self.assertEqual(self.detector.detect_os("darwin"), OS.MACOS)
        self.assertIsNone(self.detector.detect_os("idk"))


if __name__ == '__main__':
    unittest.main()
