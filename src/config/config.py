import json
from io import TextIOWrapper
from typing import Optional, Type, Any

import yaml

from src.handlers.apex.apex import ApexHandler
from src.handlers.apex.apex_config import ApexHandlerConfig
from src.handlers.handler_config import HandlerConfig
from src.handlers.ssh.ssh import SSHHandler
from src.handlers.ssh.ssh_config import SSHHandlerConfig
from src.handlers.system.system import SystemHandler
from src.kcp.kcp import KCPHandler
from src.kcp.kcp_config import KCPClientConfig, KCPServerConfig, KCPConfig
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class ConfigException(Exception):
    def __init__(self, msg: str):
        super(ConfigException, self).__init__(msg)


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


class InvalidConfigFileExtensionException(Exception):
    def __init__(self, msg: str):
        super(InvalidConfigFileExtensionException, self).__init__(msg)


class Config:
    def __init__(self, bot_logger: BotLogger):
        self._config_data: Optional[dict] = None
        self._bot_logger: BotLogger = bot_logger

    def read_config(self, file: TextIOWrapper) -> (KCPHandler, list[KCPHandler]):
        if file.name.endswith(".yaml") or file.name.endswith(".yml"):
            with file as f:
                self._config_data = yaml.load(f, Loader=yaml.SafeLoader)
        elif file.name.endswith(".json"):
            with file as f:
                self._config_data = json.loads(f.read())
        else:
            file.close()
            raise InvalidConfigFileExtensionException(f"Config file does not have a valid extension [.json/.yaml]")
        return self._process_server(), self._process_clients()

    def _process_server(self) -> KCPHandler:
        server: dict = self._get_key(self._config_data, "server", dict)
        handler: str = self._get_key(server, "handler")
        kcp_config: KCPConfig = self._get_kcp_config(server, "server")
        kcp_handler, handler_config = self._get_handler_config(server, handler)  # type: Type[KCPHandler], HandlerConfig
        return kcp_handler(self._bot_logger, ServiceMode.SERVER, kcp_config, handler_config)

    def _process_clients(self) -> list[KCPHandler]:
        clients: list = self._get_key(self._config_data, "clients", list)
        client_handlers: list[KCPHandler] = []
        for client in clients:
            client_handlers.append(self._process_client(client))
        return client_handlers

    def _process_client(self, client: dict) -> KCPHandler:
        handler: str = self._get_key(client, "handler")
        kcp_config: KCPConfig = self._get_kcp_config(client, "client")
        kcp_handler, handler_config = self._get_handler_config(client, handler)  # type: Type[KCPHandler], HandlerConfig
        return kcp_handler(self._bot_logger, ServiceMode.CLIENT, kcp_config, handler_config)

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

    def _get_handler_config(self, instance: dict, handler_type: str) -> (Type[KCPHandler], HandlerConfig):
        if handler_type == "system":
            return SystemHandler, HandlerConfig()
        elif handler_type == "ssh":
            conf: dict = self._get_key(instance, "config", dict)
            ssh_user: str = self._get_key(conf, "ssh_user")
            ssh_pass: str = self._get_key(conf, "ssh_pass")
            ssh_host: str = self._get_key(conf, "ssh_host")
            ssh_port: int = self._get_key(conf, "ssh_port", int)
            return SSHHandler, SSHHandlerConfig(ssh_user, ssh_pass, ssh_host, ssh_port)
        elif handler_type == "apex":
            conf: dict = self._get_key(instance, "config", dict)
            panel_user: str = self._get_key(conf, "panel_user")
            panel_pass: str = self._get_key(conf, "panel_pass")
            return ApexHandler, ApexHandlerConfig(panel_user, panel_pass)
        else:
            raise InvalidHandlerException(f"Unable to parse config for handler named: {handler_type}!")

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
