from src.handlers.handler_config import HandlerConfig


class ApexHandlerConfig(HandlerConfig):
    def __init__(self, panel_user: str, panel_pass: str):
        super(ApexHandlerConfig, self).__init__()
        self.panel_user: str = panel_user
        self.panel_pass: str = panel_pass
