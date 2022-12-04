from src.logger.bot_logger import BotLogger


class KCP:
    def __init__(self, bot_logger: BotLogger):
        self.bot_logger: BotLogger = bot_logger
        self._download_bin()

    def _download_bin(self):
        raise NotImplementedError

    def run_kcp(self):
        raise NotImplementedError
