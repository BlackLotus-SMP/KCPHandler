import unittest

from src.helpers.detector import Detector, Arch


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.detector: Detector = Detector()

    def test_0_arch(self):
        self.assertEqual(self.detector.detect_arch("armv5idk"), Arch.ARMV5)
        self.assertIsNone(self.detector.detect_arch("idkarmv5"), Arch.ARMV5)
        self.assertEqual(self.detector.detect_arch("armv7"), Arch.ARMV7)
        self.assertEqual(self.detector.detect_arch("i386"), Arch.A386)
        self.assertEqual(self.detector.detect_arch("x86"), Arch.A386)
        self.assertEqual(self.detector.detect_arch("x86_64"), Arch.AMD64)
        self.assertIsNone(self.detector.detect_arch("idk"))


if __name__ == '__main__':
    unittest.main()
