import unittest

from src.config.config import Config, KCPConfigException, KeyNotFoundException, KeyNotValidTypeException
from src.handlers.handler_config import HandlerConfig
from src.handlers.ssh.ssh import SSHHandler
from src.handlers.ssh.ssh_config import SSHHandlerConfig
from src.handlers.system.system import SystemHandler
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

    def test_3_kcp_value_validation(self):
        instance: dict = {"kcp": {"target": "1.2.3.4:25566", "listen": ":25566", "password": "test123"}}
        kcp_data: dict = instance.get("kcp")
        client: KCPConfig = self.config.get_kcp_config(instance, "client")
        server: KCPConfig = self.config.get_kcp_config(instance, "server")
        self.assertEqual(client.remote, kcp_data.get("target"))
        self.assertEqual(server.remote, kcp_data.get("target"))
        self.assertEqual(client.listen, kcp_data.get("listen"))
        self.assertEqual(server.listen, kcp_data.get("listen"))
        self.assertEqual(client.key, kcp_data.get("password"))
        self.assertEqual(server.key, kcp_data.get("password"))

    def test_4_system_handler(self):
        instance: dict = {"handler": "system"}
        handler, config = self.config.get_handler_config(instance)
        self.assertEqual(handler, SystemHandler)
        self.assertDictEqual(config.__dict__, HandlerConfig().__dict__)

    def test_5_ssh_handler(self):
        instance: dict = {
            "handler": "ssh",
            "config": {
                "ssh_user": "user",
                "ssh_pass": "pass",
                "ssh_host": "127.0.0.1",
                "ssh_port": 5555
            }
        }
        config_data: dict = instance.get("config")
        handler, config = self.config.get_handler_config(instance)
        self.assertEqual(handler, SSHHandler)
        ssh_config: SSHHandlerConfig = SSHHandlerConfig(
            config_data.get("ssh_user"),
            config_data.get("ssh_pass"),
            config_data.get("ssh_host"),
            config_data.get("ssh_port")
        )
        self.assertDictEqual(config.__dict__, ssh_config.__dict__)

        config_data["ssh_port"] = "5555"
        self.assertDictEqual(config.__dict__, ssh_config.__dict__)

        config_data["ssh_port"] = "5555xd"
        instance["config"] = config_data
        self.assertRaises(KeyNotValidTypeException, self.config.get_handler_config, instance)

        config_data.pop("ssh_port")
        instance["config"] = config_data
        self.assertRaises(KeyNotFoundException, self.config.get_handler_config, instance)


if __name__ == "__main__":
    unittest.main()
