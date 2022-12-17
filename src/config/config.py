import os.path
from typing import Final, Optional

import yaml

from src.handlers.apex_hosting.apex_config import ApexHandlerConfig
from src.handlers.handler_config_interface import HandlerConfig
from src.handlers.ssh.ssh_config import SSHHandlerConfig
from src.kcp.kcp_config import KCPClientConfig, KCPServerConfig, KCPConfig


class KCPConfigException(Exception):
    def __init__(self, msg: str):
        super(KCPConfigException, self).__init__(msg)


class KeyNotFoundException(Exception):
    def __init__(self, msg: str):
        super(KeyNotFoundException, self).__init__(msg)


class InvalidHandlerException(Exception):
    def __init__(self, msg: str):
        super(InvalidHandlerException, self).__init__(msg)


class InvalidConfigHandlerException(Exception):
    def __init__(self, msg: str):
        super(InvalidConfigHandlerException, self).__init__(msg)


class Config:
    def __init__(self):
        self._CONFIG_NAME: Final = "config.yml"
        self._config_data: Optional[dict] = None

    def read_config(self):
        if not os.path.isfile(self._CONFIG_NAME):
            raise Exception("Create sample")
        with open(self._CONFIG_NAME, "r") as cfg:
            self._config_data = yaml.load(cfg, Loader=yaml.SafeLoader)
        print(self._config_data)
        self._process_server()
        self._process_clients()
        # print(type(self._config_data))

    def _process_server(self):
        server: dict = self._get_key(self._config_data, "server")
        handler: str = self._get_key(server, "handler")
        kcp_config: KCPConfig = self._get_kcp_config(server, "server")
        handler_config: HandlerConfig = self._get_handler_config(server, handler)

    def _process_clients(self):
        clients: list = self._get_key(self._config_data, "clients")
        for client in clients:
            self._process_client(client)

    def _process_client(self, client: dict):
        handler: str = self._get_key(client, "handler")
        kcp_config: KCPConfig = self._get_kcp_config(client, "client")
        handler_config: HandlerConfig = self._get_handler_config(client, handler)

    @classmethod
    def _get_key(cls, instance: dict[str, str], key: str) -> str | dict | list:
        k: str = instance.get(key)
        if not k:
            raise KeyNotFoundException(f"{key} not found!")
        return k

    def _get_handler_config(self, instance: dict, handler_type: str) -> HandlerConfig:
        if handler_type == "system":
            return HandlerConfig()
        elif handler_type == "ssh":
            conf: dict = self._get_config(instance, handler_type)
            return SSHHandlerConfig()
        elif handler_type == "apex":
            conf: dict = self._get_config(instance, handler_type)
            return ApexHandlerConfig()
        else:
            raise InvalidHandlerException(f"Unable to parse config for handler named: {handler_type}!")

    @classmethod
    def _get_config(cls, instance: dict, handler_type: str) -> dict:
        config: dict = instance.get("config")
        if not config:
            raise InvalidConfigHandlerException(f"Config not found for {handler_type}!")
        return config

    def _get_kcp_config(self, instance: dict, svc_type: str) -> KCPConfig:
        kcp_config: dict = self._get_key(instance, "kcp")
        listen_addr: str = self._get_key(kcp_config, "listen")
        password: str = self._get_key(kcp_config, "password")
        target_addr: str = kcp_config.get("target")
        remote_addr: str = kcp_config.get("remote")
        if not target_addr and not remote_addr:
            raise KCPConfigException("Target or remote kcp config not found")
        if target_addr:
            remote_addr: str = target_addr
        if svc_type == "client":
            return KCPClientConfig(remote_addr, listen_addr, password)
        else:
            return KCPServerConfig(remote_addr, listen_addr, password)
