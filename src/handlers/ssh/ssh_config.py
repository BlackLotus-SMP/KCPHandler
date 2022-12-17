from src.handlers.handler_config_interface import HandlerConfig


class SSHHandlerConfig(HandlerConfig):
    def __init__(self, ssh_user: str, ssh_pass: str, ssh_host: str, ssh_port: int):
        super(SSHHandlerConfig, self).__init__()
        self.ssh_user: str = ssh_user
        self.ssh_pass: str = ssh_pass
        self.ssh_port: int = ssh_port
        self.ssh_host: str = ssh_host
