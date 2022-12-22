import unittest

from src.config.config import Config, KCPConfigException, KeyNotFoundException
from src.kcp.kcp_config import KCPClientConfig, KCPServerConfig, KCPConfig
from src.logger.bot_logger import BotLogger


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config: Config = Config(BotLogger())

    def test_0_client_kcp(self):
        instance: dict = {"kcp": {"remote": "1.2.3.4:25566", "listen": ":25566", "password": "test123"}}
        client: KCPClientConfig = KCPClientConfig("1.2.3.4:25566", ":25566", "test123")
        self.assertDictEqual(self.config.get_kcp_config(instance, "client").__dict__, client.__dict__)
        self.assertEqual(type(self.config.get_kcp_config(instance, "client")), KCPClientConfig)
        self.assertNotEqual(type(self.config.get_kcp_config(instance, "client")), KCPServerConfig)

    def test_1_server_kcp(self):
        instance: dict = {"kcp": {"target": "1.2.3.4:25566", "listen": ":25566", "password": "test123"}}
        server: KCPServerConfig = KCPServerConfig("1.2.3.4:25566", ":25566", "test123")
        self.assertDictEqual(self.config.get_kcp_config(instance, "server").__dict__, server.__dict__)
        self.assertEqual(type(self.config.get_kcp_config(instance, "server")), KCPServerConfig)
        self.assertNotEqual(type(self.config.get_kcp_config(instance, "server")), KCPClientConfig)

    def test_2_invalid_kcp_config(self):
        instance: dict = {"kcp": {"listen": ":25566", "password": "test123"}}
        self.assertRaises(KCPConfigException, self.config.get_kcp_config, instance, "client")
        self.assertRaises(KCPConfigException, self.config.get_kcp_config, instance, "server")
        instance: dict = {"kcp": {"listen": ":25566"}}
        self.assertRaises(KeyNotFoundException, self.config.get_kcp_config, instance, "client")
        instance: dict = {"kcp": {"password": "test123"}}
        self.assertRaises(KeyNotFoundException, self.config.get_kcp_config, instance, "server")
        instance: dict = {"kcp": {"target": "1.2.3.4:25566", "listen": ":25566", "password": "test123"}}
        self.assertRaises(KCPConfigException, self.config.get_kcp_config, instance, "idk")


if __name__ == "__main__":
    unittest.main()
