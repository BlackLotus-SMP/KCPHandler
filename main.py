from src.config.config import Config
from src.constant import BOT_NAME
from src.logger.bot_logger import BotLogger


def main():
    bot_logger = BotLogger()
    bot_logger.info(f"Started {BOT_NAME} bot")

    config: Config = Config()
    config.read_config()

    # server_config: KCPServerConfig = KCPServerConfig(target="0.0.0.0:25565", listen=":25583", password="OP_PASS")
    # server: SystemHandler = SystemHandler(bot_logger, ServiceMode.SERVER, server_config)
    # server_executor: ServerExecutor = ServerExecutor(bot_logger, server)
    # server_executor.start()
    #
    # client_executor: ClientExecutor = ClientExecutor(bot_logger)
    # client_executor.start()
    #
    # client_config: KCPClientConfig = KCPClientConfig(remote="0.0.0.0:25583", listen=":25555", password="OP_PASS")
    # client: SystemHandler = SystemHandler(bot_logger, ServiceMode.CLIENT, client_config)
    #
    # client_executor.add_handler(client)

    # server_executor.join()


if __name__ == '__main__':
    main()
