class KCPConfig:
    def __init__(self, listen: str, password: str, remote: str):
        self.mode: str = "fast3"
        self.crypt: str = "aes-192"
        self.listen: str = listen
        self.key: str = password
        self.remote: str = remote

    def __repr__(self):
        return f"Config[mode={self.mode}, crypt={self.crypt}, listen={self.crypt}, key={self.key}, remote={self.remote}]"


class KCPServerConfig(KCPConfig):
    def __init__(self, target: str, listen: str, password: str):
        super().__init__(listen, password, target)


class KCPClientConfig(KCPConfig):
    def __init__(self, remote: str, listen: str, password: str):
        super().__init__(listen, password, remote)
