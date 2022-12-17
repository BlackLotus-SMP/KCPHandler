import ftplib
import json
import os
import re
import shutil
import socket
import time
from re import Match
from typing import Final, Optional, AnyStr

import requests
from bs4 import BeautifulSoup, Tag
from requests import Response
from requests.cookies import RequestsCookieJar

from src.constant import KCP_JAR_URL
from src.handlers.apex_hosting.apex_config import ApexHandlerConfig
from src.handlers.handler_config_interface import HandlerConfig
from src.helpers.ftp import FTPProcessor, FTPFile
from src.kcp.kcp_config import KCPConfig
from src.kcp.kcp_interface import KCPHandler, GithubDownloadException, HandlerConfigNotValid
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class CloudflareException(Exception):
    def __init__(self, msg: str):
        super(CloudflareException, self).__init__(msg)


class TokenNotFoundException(Exception):
    def __init__(self, msg: str):
        super(TokenNotFoundException, self).__init__(msg)


class ServerUrlNotFoundException(Exception):
    def __init__(self, msg: str):
        super(ServerUrlNotFoundException, self).__init__(msg)


class IPNotFoundException(Exception):
    def __init__(self, msg: str):
        super(IPNotFoundException, self).__init__(msg)


class ServerModeNotValidException(Exception):
    def __init__(self, msg: str):
        super(ServerModeNotValidException, self).__init__(msg)


class CloudflareChallengeException(Exception):
    def __init__(self, msg: str):
        super(CloudflareChallengeException, self).__init__(msg)


class ApexSaveChangesException(Exception):
    def __init__(self, msg: str):
        super(ApexSaveChangesException, self).__init__(msg)


class ApexTimeoutException(Exception):
    def __init__(self, msg: str):
        super(ApexTimeoutException, self).__init__(msg)


class ApexHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, kcp_config: KCPConfig, handler_config: HandlerConfig):
        if not isinstance(handler_config, ApexHandlerConfig):
            raise HandlerConfigNotValid("Invalid handler config object for SSH handler")

        super(ApexHandler, self).__init__(bot_logger, svc_mode, kcp_config, handler_config)
        self._RESOURCES_DIR: Final = self.get_unique_name()
        self._JAR_NAME: Final = "apex_java"
        self._JAVA_VERSION: Final = "8"
        self.__handler_config: ApexHandlerConfig = handler_config

        self._bot_logger: BotLogger = bot_logger
        self._kcp_file: Optional[str] = None
        self._kcp_config: KCPConfig = kcp_config
        self._panel_user: str = self.__handler_config.panel_user
        self._panel_pass: str = self.__handler_config.panel_pass
        self._url: str = "https://panel.apexminecrafthosting.com"
        self._login_url: str = f"{self._url}/site/login"
        self._server_id: Optional[str] = ""

        if self.is_server():
            raise ServerModeNotValidException(f"Apex hosting can't be used as a server yet!")

        self._default_headers: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
            "Host": "panel.apexminecrafthosting.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "TE": "trailers",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
        self._cookies: Optional[RequestsCookieJar] = None
        self._csrf_token: Optional[str] = None

        self._server_ip: Optional[str] = ""
        self._server_port: Optional[str] = ""

    def _login(self) -> Response:
        self._bot_logger.info("Logging in apex...")
        r: Response = requests.get(self._login_url, headers=self._default_headers)
        if r.status_code == 429:
            time.sleep(40)
            raise CloudflareException("requests status code 429!")
        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")
        token_input: Tag = soup.find("input", attrs={"type": "hidden", "name": "YII_CSRF_TOKEN"})
        if not token_input:
            raise TokenNotFoundException(f"Unable to find a valid token")
        self._csrf_token: Optional[str] = token_input.get("value")
        self._cookies: Optional[RequestsCookieJar] = r.cookies.copy()
        self._resolve_challenge(r)
        login_data: dict[str, str] = {
            "YII_CSRF_TOKEN": self._csrf_token,
            "LoginForm[name]": self._panel_user,
            "LoginForm[password]": self._panel_pass,
            "LoginForm[rememberMe]": "1",
            "LoginForm[ignoreIp]": "1",
            "yt0": "Login"
        }
        self._default_headers.update({"Sec-Fetch-Site": "same-origin"})
        self._default_headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        self._default_headers.update({"Origin": "null"})
        self._bot_logger.info("Log in attempt")
        cookie_capture: Response = requests.post(self._login_url, headers=self._default_headers, data=login_data, cookies=self._cookies, allow_redirects=False)
        self._cookies.update(cookie_capture.cookies.copy())
        log: Response = requests.post(self._login_url, headers=self._default_headers, data=login_data, cookies=self._cookies)
        self._default_headers.pop("Content-Type")
        self._default_headers.pop("Origin")
        self._cookies.update(log.cookies.copy())
        self._bot_logger.info("Logged in!")
        return log

    def _resolve_challenge(self, login_panel):
        self._bot_logger.info("Bypassing cloudflare antibot challenge...")
        s: BeautifulSoup = BeautifulSoup(login_panel.text, "html.parser")
        challenge_id: str = ""
        for script in s.find_all("script"):
            challenge_id_find: Optional[Match[AnyStr]] = re.search(r"r:\'([a-zA-Z0-9]+)\'", script.text)
            if not challenge_id_find:
                continue
            challenge_id: str = challenge_id_find.group(1)
        if not challenge_id:
            raise CloudflareChallengeException("Challenge ID not found!")
        challenge: str = f"{self._url}/cdn-cgi/challenge-platform/h/b/cv/result/{challenge_id}"
        r: Response = requests.post(challenge, headers=self._default_headers, cookies=self._cookies)
        if r.status_code != 200:
            raise CloudflareChallengeException("Unable to retrieve cookies from challenge!")
        self._cookies.update(r.cookies.copy())
        self._bot_logger.info("Done!")

    @classmethod
    def _get_server_url(cls, login_response: Response) -> str:
        uri: Optional[Match[AnyStr]] = re.search(r"/server/\d+", login_response.text)
        if not uri:
            raise ServerUrlNotFoundException("Unable to find a valid server url!")
        return uri.group(0)

    @classmethod
    def _get_redirect_url(cls, login_response: Response) -> str:
        uri: Optional[Match[AnyStr]] = re.search(r"/server/index/\d+", login_response.text)
        if not uri:
            raise ServerUrlNotFoundException("Unable to find a valid server url!")
        return uri.group(0)

    def _get_ftp_creds(self, login_response: Response) -> (str, str, str, str):
        self._bot_logger.info("Retrieving FTP credentials")
        ip_finder: Optional[Match[AnyStr]] = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}", login_response.text)
        if not ip_finder:
            raise IPNotFoundException("")
        server_ip: str = ip_finder.group(0).split(":")[0]
        server_port: str = ip_finder.group(0).split(":")[1]
        ftp_port: str = "21"
        ftp_user: str = f"{self._panel_user.title()}.{self._server_id}"
        self._bot_logger.info("FTP credentials retrieved")
        return server_ip, server_port, ftp_port, ftp_user

    def _do_redirect(self, url: str):
        r: Response = requests.get(url, headers=self._default_headers, cookies=self._cookies)
        self._cookies.update(r.cookies)

    def _save_changes(self, login_response, jar_name: str) -> dict[str, str]:
        s: BeautifulSoup = BeautifulSoup(login_response.text, "html.parser")
        location_selected: str = s.find("option", attrs={"data-transfer-type": "location", "selected": True}).get("data-location")
        server_name: str = s.find("input", attrs={"name": "Server[name]"}).get("value")
        server_players: str = s.find("input", attrs={"name": "Server[players]"}).get("value")
        server_domain: str = s.find("input", attrs={"name": "Server[domain]"}).get("value")
        world_name: str = s.find("input", attrs={"id": "world-name"}).get("value")
        kick_delay: str = s.find("input", attrs={"name": "Server[kick_delay]"}).get("value")
        apply_jar: dict[str, str] = {
            "YII_CSRF_TOKEN": self._csrf_token,
            "goto_setup": "",
            "confirm_leave": "true",
            "location": f"location_{location_selected.replace(' ', '+')}",
            "Server[name]": server_name.replace(' ', '+'),
            "Server[players]": server_players.replace(' ', '+'),
            "Server[domain]": server_domain.replace(' ', '+'),
            "Server[world]": world_name.replace(' ', '+'),
            "jar-select": "custom.jar",
            "Server[jarfile]": jar_name,
            "Server[kick_delay]": kick_delay.replace(' ', '+'),
            "Server[autosave]": "0",
            "Server[announce_save]": "0",
            "ServerConfig[ip_auth_role]": "mod",
            "cheat_role": "0",
            "yt4": "Save"
        }
        return apply_jar

    def _ftp_upload(self, server_ip: str, ftp_user: str):
        self._bot_logger.info("Logging in the FTP server")
        with ftplib.FTP(host=server_ip, user=ftp_user, passwd=self._panel_pass) as ftp:
            ftp_processor: FTPProcessor = FTPProcessor(ftp)

            root_files: list[FTPFile] = ftp_processor.list_files()
            jar_dir_found: bool = False
            data_dir_found: bool = False
            for f in root_files:
                if f.is_dir() and f.get_name() == "jar":
                    jar_dir_found: bool = True
                if f.is_dir() and f.get_name() == "data":
                    data_dir_found: bool = True
            if not jar_dir_found:
                self._bot_logger.info("jar dir not found! creating...")
                ftp_processor.create_dir("jar")
            if not data_dir_found:
                self._bot_logger.info("data dir not found! creating...")
                ftp_processor.create_dir("data")

            data_files: list[FTPFile] = ftp_processor.list_files("data")
            config_dir_found: bool = False
            for f in data_files:
                if f.is_dir() and f.get_name() == "config":
                    config_dir_found: bool = True

            if not config_dir_found:
                self._bot_logger.info("data/config dir not found! creating...")
                ftp_processor.create_dir("config", base_path="data")

            config_files: list[FTPFile] = ftp_processor.list_files("data/config")
            config_file_found: bool = False
            for f in config_files:
                if not f.is_dir() and f.get_name() == "config.json":
                    config_file_found: bool = True
            if config_file_found:
                self._bot_logger.info("old data/config/config.json found! reloading file...")
                ftp_processor.delete_file("data/config/config.json")

            jar_files: list[FTPFile] = ftp_processor.list_files("jar")
            jar_found: bool = False
            for f in jar_files:
                if not f.is_dir() and f.get_name() == f"{self._JAR_NAME}-{self._JAVA_VERSION}.jar":
                    jar_found: bool = True
            if jar_found:
                self._bot_logger.info(f"old jar/{self._JAR_NAME}-{self._JAVA_VERSION}.jar found! reloading file...")
                ftp_processor.delete_file(f"jar/{self._JAR_NAME}-{self._JAVA_VERSION}.jar")

            config: dict[str, str] = {
                "remoteaddr": self._kcp_config.remote,
                "localaddr": self._kcp_config.listen,
                "mode": self._kcp_config.mode,
                "crypt": self._kcp_config.crypt,
                "key": self._kcp_config.key
            }
            with open(f"{self._RESOURCES_DIR}/config.json", "w") as f:
                f.write(json.dumps(config, indent=2))

            self._bot_logger.info(f"Uploading jar/{self._JAR_NAME}-{self._JAVA_VERSION}.jar...")
            ftp_processor.upload_file(
                f"{self._RESOURCES_DIR}/{self._JAR_NAME}-{self._JAVA_VERSION}.jar",
                f"{self._JAR_NAME}-{self._JAVA_VERSION}.jar",
                "jar"
            )
            self._bot_logger.info(f"Uploading data/config/config.json...")
            ftp_processor.upload_file(f"{self._RESOURCES_DIR}/config.json", "config.json", "data/config")
            os.remove(f"{self._RESOURCES_DIR}/config.json")
        os.remove(f"{self._RESOURCES_DIR}/{self._JAR_NAME}-{self._JAVA_VERSION}.jar")

    def download_bin(self):
        dashboard: Response = self._login()
        server_url: str = f"{self._url}{self._get_server_url(dashboard)}"
        redirect_server_url: str = f"{self._url}{self._get_redirect_url(dashboard)}"
        self._do_redirect(redirect_server_url)
        self._resolve_challenge(dashboard)
        self._server_id: str = server_url.split("/")[-1]
        self._default_headers.update({"Referer": f"{self._url}/server/{self._server_id}"})
        server_ip, server_port, ftp_port, ftp_user = self._get_ftp_creds(dashboard)
        self._server_ip: str = server_ip
        self._server_port: str = server_port
        self._bot_logger.info(f"Downloading a valid jar with GO KCP binary for java {self._JAVA_VERSION}")
        try:
            r = requests.get(KCP_JAR_URL)
        except Exception as e:
            self._bot_logger.error(f"Unable to get valid KCP assets {e}")
            raise GithubDownloadException(f"Unable to get valid KCP assets {e}")
        if r.status_code != 200:
            raise GithubDownloadException(f"Unable to get a valid release, got status code {r.status_code}!")
        download_url: str = ""
        for release in r.json():
            if release.get("name") == f"java-{self._JAVA_VERSION}":
                download_url: str = release.get("assets")[0].get("browser_download_url")
                break
        if not download_url:
            raise GithubDownloadException(f"Unable to get valid KCP assets")

        if not os.path.isdir(self._RESOURCES_DIR):
            os.mkdir(self._RESOURCES_DIR)
        if os.path.isfile(f"{self._RESOURCES_DIR}/{self._JAR_NAME}-{self._JAVA_VERSION}.jar"):
            os.remove(f"{self._RESOURCES_DIR}/{self._JAR_NAME}-{self._JAVA_VERSION}.jar")

        kcp_jar: Response = requests.get(download_url, stream=True)
        with open(f"{self._RESOURCES_DIR}/{self._JAR_NAME}-{self._JAVA_VERSION}.jar", "wb") as f:
            for chunk in kcp_jar.iter_content(chunk_size=2048):
                if chunk:
                    f.write(chunk)

        self._bot_logger.info("Uploading assets to the apex FTP server...")
        self._ftp_upload(server_ip, ftp_user)
        self._bot_logger.info("Uploaded! everything is up to date")
        self._bot_logger.info("Applying changes")
        self._default_headers.update({"Sec-Fetch-Dest": "empty"})
        self._default_headers.update({"Sec-Fetch-Mode": "cors"})
        self._default_headers.update({"X-Requested-With": "XMLHttpRequest"})
        self._default_headers.update({"Origin": self._url})
        self._default_headers.update({"Alt-Used": self._url})
        self._default_headers.update({"Accept": "*/*"})
        apply_changes: dict[str, str] = self._save_changes(dashboard, f"{self._JAR_NAME}-{self._JAVA_VERSION}.jar")
        applied = requests.post(server_url, headers=self._default_headers, data=apply_changes, cookies=self._cookies)
        if applied.status_code != 200:
            raise ApexSaveChangesException("Unable to save changes for new config!")
        self._bot_logger.info("Setup done, ready to run! :)")
        if os.path.isdir(self._RESOURCES_DIR):
            shutil.rmtree(self._RESOURCES_DIR)

    def run_kcp(self):
        self._bot_logger.info("Sending restart signal!")
        url: str = f"{self._url}/server/{self._server_id}"
        restart_data: dict[str, str] = {
            "ajax": "restart",
            "YII_CSRF_TOKEN": self._csrf_token
        }
        _ = requests.post(url, headers=self._default_headers, cookies=self._cookies, data=restart_data)
        self._bot_logger.info("starting Apex KCP service, should be up in some minutes!")
        timeout: int = 10
        while True:
            if timeout < 0:
                # 5 minutes wait until process crashes and restarts!
                time.sleep(60 * 5)
                raise ApexTimeoutException("KCP Node timed out 10 times! crashing...")
            try:
                time.sleep(20)
                socket.setdefaulttimeout(30)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self._server_ip, int(self._server_port)))
            except Exception as e:
                _ = e
                timeout -= 1
                self._bot_logger.warning(f"Apex KCP listener did not respond timeout: {10-timeout}/10")
            else:
                s.close()
                timeout: int = 10
