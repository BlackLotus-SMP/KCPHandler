import os.path
from typing import Final, Optional

import yaml

from src.handlers.handler_config_interface import HandlerConfig
from src.kcp.kcp_config import KCPClientConfig, KCPServerConfig, KCPConfig


class ServerNotFoundException(Exception):
    def __init__(self, msg: str):
        super(ServerNotFoundException, self).__init__(msg)


class ClientsNotFoundException(Exception):
    def __init__(self, msg: str):
        super(ClientsNotFoundException, self).__init__(msg)


class KCPConfigNotFoundException(Exception):
    def __init__(self, msg: str):
        super(KCPConfigNotFoundException, self).__init__(msg)


class KCPConfigException(Exception):
    def __init__(self, msg: str):
        super(KCPConfigException, self).__init__(msg)


class HandlerNotFoundException(Exception):
    def __init__(self, msg: str):
        super(HandlerNotFoundException, self).__init__(msg)


class InvalidHandlerException(Exception):
    def __init__(self, msg: str):
        super(InvalidHandlerException, self).__init__(msg)


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
        server: dict = self._config_data.get("server")
        if not server:
            raise ServerNotFoundException("Server yaml not configured properly!")
        handler: str = self._get_handler(server)
        kcp_config: KCPConfig = self._get_kcp_config(server, "server")
        handler_config: HandlerConfig = self._get_handler_config(server, handler)

    def _process_clients(self):
        clients: list = self._config_data.get("clients")
        if not clients:
            raise ClientsNotFoundException("Clients yaml not configured properly")
        for client in clients:
            self._process_client(client)

    def _process_client(self, client: dict):
        handler: str = self._get_handler(client)
        kcp_config: KCPConfig = self._get_kcp_config(client, "client")
        handler_config: HandlerConfig = self._get_handler_config(client, handler)

    @classmethod
    def _get_handler(cls, instance: dict[str, str]) -> str:
        handler: str = instance.get("handler")
        if not handler:
            raise HandlerNotFoundException("Handler not found")
        return handler

    def _get_handler_config(self, instance: dict, handler_type: str) -> HandlerConfig:
        if handler_type == "system":
            return HandlerConfig()
        elif handler_type == "ssh":
            conf: dict = self._get_config(instance, handler_type)
        elif handler_type == "apex":
            conf: dict = self._get_config(instance, handler_type)
        else:
            raise InvalidHandlerException(f"Unable to parse config for handler named: {handler_type}!")

    @classmethod
    def _get_config(cls, instance: dict, handler_type: str) -> dict:
        config: dict = instance.get("config")
        if not config:
            raise InvalidHandlerException(f"Config not found for {handler_type}!")
        return config

    @classmethod
    def _get_kcp_config(cls, instance: dict, svc_type: str) -> KCPConfig:
        kcp_config: dict = instance.get("kcp")
        if not kcp_config:
            raise KCPConfigNotFoundException("KCP not found")
        listen_addr: str = kcp_config.get("listen")
        if not listen_addr:
            raise KCPConfigException("Listen kcp config not found")
        target_addr: str = kcp_config.get("target")
        remote_addr: str = kcp_config.get("remote")
        if not target_addr and not remote_addr:
            raise KCPConfigException("Target or remote kcp config not found")
        if target_addr:
            remote_addr: str = target_addr
        password: str = kcp_config.get("password")
        if not password:
            raise KCPConfigException("Password kcp config not found")
        if svc_type == "client":
            return KCPClientConfig(remote_addr, listen_addr, password)
        else:
            return KCPServerConfig(remote_addr, listen_addr, password)
