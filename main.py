from argparse import ArgumentParser, FileType, Namespace

from src.config.config import Config
from src.constant import BOT_NAME
from src.kcp.kcp import KCPHandler
from src.logger.bot_logger import BotLogger
from src.thread_executor.client_executor import ClientExecutor
from src.thread_executor.server_executor import ServerExecutor


def main():
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument("-c", "--config", help="path of the config file", type=FileType("r"), default="config.yml")
    args: Namespace = parser.parse_args()

    bot_logger = BotLogger()
    bot_logger.info(f"Started {BOT_NAME} bot")

    config: Config = Config(bot_logger)
    server, clients = config.read_config(args.config)  # type: KCPHandler, list[KCPHandler]

    server_executor: ServerExecutor = ServerExecutor(bot_logger, server)
    server_executor.start()

    client_executor: ClientExecutor = ClientExecutor(bot_logger)
    client_executor.start()

    for client in clients:
        client_executor.add_handler(client)

    server_executor.join()


if __name__ == '__main__':
    main()
