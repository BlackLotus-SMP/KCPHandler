import os.path
from typing import Final, Optional, Type, Any

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


class KeyNotValidTypeException(Exception):
    def __init__(self, msg: str):
        super(KeyNotValidTypeException, self).__init__(msg)


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
        server: dict = self._get_key(self._config_data, "server", dict)
        handler: str = self._get_key(server, "handler")
        kcp_config: KCPConfig = self._get_kcp_config(server, "server")
        handler_config: HandlerConfig = self._get_handler_config(server, handler)

    def _process_clients(self):
        clients: list = self._get_key(self._config_data, "clients", list)
        for client in clients:
            self._process_client(client)

    def _process_client(self, client: dict):
        handler: str = self._get_key(client, "handler")
        kcp_config: KCPConfig = self._get_kcp_config(client, "client")
        handler_config: HandlerConfig = self._get_handler_config(client, handler)

    @classmethod
    def _get_key(cls, instance: dict[str, str], key: str, type_: Type = str) -> Any:
        k: Any = instance.get(key)
        if not k:
            raise KeyNotFoundException(f"{key} not found!")
        if type_ == int and type(k) == str and k.isnumeric():
            k = int(k)
        key_type: Type = type(k)
        if key_type != type_:
            raise KeyNotValidTypeException(f"{key} has an invalid type! found {key_type}, expected {type_}")
        return k

    def _get_handler_config(self, instance: dict, handler_type: str) -> HandlerConfig:
        if handler_type == "system":
            return HandlerConfig()
        elif handler_type == "ssh":
            conf: dict = self._get_config(instance, handler_type)
            ssh_user: str = self._get_key(conf, "ssh_user")
            ssh_pass: str = self._get_key(conf, "ssh_pass")
            ssh_host: str = self._get_key(conf, "ssh_host")
            ssh_port: int = self._get_key(conf, "ssh_port", int)
            return SSHHandlerConfig(ssh_user, ssh_pass, ssh_host, ssh_port)
        elif handler_type == "apex":
            conf: dict = self._get_config(instance, handler_type)
            panel_user: str = self._get_key(conf, "panel_user")
            panel_pass: str = self._get_key(conf, "panel_pass")
            return ApexHandlerConfig(panel_user, panel_pass)
        else:
            raise InvalidHandlerException(f"Unable to parse config for handler named: {handler_type}!")

    @classmethod
    def _get_config(cls, instance: dict, handler_type: str) -> dict:
        config: dict = instance.get("config")
        if not config:
            raise InvalidConfigHandlerException(f"Config not found for {handler_type}!")
        return config

    def _get_kcp_config(self, instance: dict, svc_type: str) -> KCPConfig:
        kcp_config: dict = self._get_key(instance, "kcp", dict)
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
