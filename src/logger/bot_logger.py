import sys
from logging import Logger, StreamHandler

from colorlog import ColoredFormatter

from src.constant import BOT_NAME


class BotLogger(Logger):
    def __init__(self):
        super(BotLogger, self).__init__(BOT_NAME)
        self._LOG_COLORS = {
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "bold_yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }

        self._SECONDARY_LOG_COLORS = {
            "message": {
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red"
            }
        }

        self._console_handler = StreamHandler(sys.stdout)
        self._console_handler.setFormatter(
            fmt=ColoredFormatter(
                "[%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]: %(message_log_color)s%(message)s%(reset)s",
                log_colors=self._LOG_COLORS,
                secondary_log_colors=self._SECONDARY_LOG_COLORS,
                datefmt="%H:%M:%S"
            )
        )
        self.addHandler(self._console_handler)
