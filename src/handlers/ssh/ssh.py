import os
import re
import shutil
import tarfile
from typing import Optional

import requests
from paramiko.channel import Channel
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.sftp_client import SFTPClient

from src.kcp.kcp_config import KCPConfig
from src.constant import KCPTUN_URL
from src.handlers.handler_config_interface import HandlerConfig
from src.kcp.kcp_interface import KCPHandler, InvalidSystemException, GithubDownloadException, HandlerConfigNotValid
from src.kcp.process_interface import KCPProcess
from src.handlers.ssh.ssh_config import SSHHandlerConfig
from src.helpers.detector import Detector, Arch, OS
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class KCPSSHProcess(KCPProcess):
    def __init__(self, bot_logger: BotLogger, is_client: bool, kcp_config: KCPConfig, ssh_client: SSHClient):
        super().__init__(bot_logger, is_client, kcp_config)
        self._ssh_client: SSHClient = ssh_client

    def start(self, kcp_path: str):
        if self._is_client:
            kcp_command: str = f"./{kcp_path} -r {self._kcp_config.remote} -l {self._kcp_config.listen} -mode {self._kcp_config.mode} --crypt {self._kcp_config.crypt} --key {self._kcp_config.key}"
        else:
            kcp_command: str = f"./{kcp_path} -t {self._kcp_config.remote} -l {self._kcp_config.listen} -mode {self._kcp_config.mode} --crypt {self._kcp_config.crypt} --key {self._kcp_config.key}"

        chan: Channel = self._ssh_client.invoke_shell()
        chan.send(bytes(kcp_command + "\n", "utf-8"))
        buffer: str = ""
        is_running: bool = True
        while is_running:
            buffer += chan.recv(2048).decode("utf-8")
            lines: list[str] = buffer.split("\r\n")
            if len(lines) > 1:
                buffer: str = lines[-1]
                for line in lines[:-1]:
                    # self._bot_logger.info(line)
                    if line.lower() == "terminated":
                        is_running = False
        chan.close()
        self._ssh_client.close()


class SSHHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, kcp_config: KCPConfig, handler_config: HandlerConfig):
        if not isinstance(handler_config, SSHHandlerConfig):
            raise HandlerConfigNotValid("Invalid handler config object for SSH handler")

        super(SSHHandler, self).__init__(bot_logger, svc_mode, kcp_config, handler_config)
        self.__handler_config: SSHHandlerConfig = handler_config
        self._bot_logger: BotLogger = bot_logger
        self._kcp_file: Optional[str] = None
        self._kcp_config: KCPConfig = kcp_config

        self._ssh_user: str = self.__handler_config.ssh_user
        self._ssh_pass: str = self.__handler_config.ssh_pass
        self._ssh_port: int = self.__handler_config.ssh_port
        self._ssh_host: str = self.__handler_config.ssh_host

        self._ssh_client: Optional[SSHClient] = None
        self._bin_remote_path: Optional[str] = None

    def _simple_command(self, command: str) -> str:
        stdin, stdout, stderr = self._ssh_client.exec_command(command)
        stdin.close()
        output: str = ""
        for line in iter(lambda: stdout.readline(2048), ""):
            output += line
        stdout.close()
        stderr.close()
        return output

    def download_bin(self):
        self._ssh_client: SSHClient = SSHClient()
        self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        self._ssh_client.connect(hostname=self._ssh_host, port=self._ssh_port, username=self._ssh_user, password=self._ssh_pass)
        detector: Detector = Detector()
        arch: Arch = detector.detect_arch(self._simple_command("uname -m"))
        os_: OS = detector.detect_os(self._simple_command("uname -s"))
        if not arch or not os_:
            raise InvalidSystemException(f"Unable to find a valid os or arch, information found: os={os_.value}, arch={arch.value}, report with your 'uname -s' and 'uname -m'")
        self._bot_logger.info(f"Found {os_.value} with {arch.value}")
        try:
            r = requests.get(KCPTUN_URL)
        except Exception as e:
            self._bot_logger.error(f"Unable to get valid KCP assets {e}")
            raise GithubDownloadException(f"Unable to get valid KCP assets {e}")
        if r.status_code != 200:
            raise GithubDownloadException(f"Unable to get a valid release, got status code {r.status_code}!")
        data: dict = r.json()
        assets: list[dict] = data.get("assets")
        ver: str = rf"^kcptun-{os_.value}-{arch.value}-\d+.tar.gz$"
        download_url: str = ""
        for asset in assets:
            asset_name: str = asset.get("name")
            if re.search(ver, asset_name):
                download_url = asset.get("browser_download_url")
                break
        if not download_url:
            raise InvalidSystemException(f"Couldn't find a valid version for this os and arch, information found: os={os_.value}, arch={arch.value}, report with your 'uname -s' and 'uname -m'")
        self._bot_logger.info("Found a valid release!")
        self._bot_logger.info(f"Downloading {download_url}...")
        resources_dir: str = self.get_unique_name()
        if os.path.isdir(resources_dir):
            shutil.rmtree(resources_dir)
        if not os.path.isdir(resources_dir):
            os.mkdir(resources_dir)
        kcp_compressed = requests.get(download_url, stream=True)
        with open(f"{resources_dir}/compressed.tar.gz", "wb") as f:
            for chunk in kcp_compressed.iter_content(chunk_size=2048):
                if chunk:
                    f.write(chunk)
        self._bot_logger.info(f"File downloaded")
        file: tarfile.TarFile = tarfile.open(f"{resources_dir}/compressed.tar.gz")
        file.extractall(path=resources_dir)
        file.close()
        os.remove(f"{resources_dir}/compressed.tar.gz")
        self._bot_logger.info(f"Extracting a valid binary")
        files: list[str] = os.listdir(resources_dir)
        expected_binary_format: str = "client" if self.is_client() else "server"
        expected_binary_format += f"_{os_.value}_{arch.value}"
        kcp_file: str = ""
        for bin_file in files:
            if bin_file.startswith(expected_binary_format):
                kcp_file = f"{resources_dir}/{bin_file}"
            else:
                os.remove(f"{resources_dir}/{bin_file}")
        bin_name: str = kcp_file.split('/')[-1]
        if not kcp_file:
            raise InvalidSystemException(f"Couldn't find a valid executable! information found: os={os_.value}, arch={arch.value}, report with your 'uname -s' and 'uname -m', files found: {', '.join(files)}!")
        _ = self._simple_command("mkdir -p auto_kcp")
        _ = self._simple_command("rm -rf auto_kcp/client*")
        _ = self._simple_command("rm -rf auto_kcp/server*")
        self._bot_logger.info("Uploading bin file to the server")
        self._bin_remote_path: str = f"auto_kcp/{bin_name}"
        ftp: SFTPClient = self._ssh_client.open_sftp()
        ftp.put(localpath=kcp_file, remotepath=self._bin_remote_path)
        ftp.close()
        shutil.rmtree(resources_dir)
        self._bot_logger.info("+x perms to the bin file")
        _ = self._simple_command(f"chmod +x {self._bin_remote_path}")
        self._bot_logger.info(f"{self._bin_remote_path} ready!")

    def run_kcp(self):
        kcp_process: KCPSSHProcess = KCPSSHProcess(self._bot_logger, self.is_client(), self._kcp_config, self._ssh_client)
        kcp_process.start(self._bin_remote_path)
