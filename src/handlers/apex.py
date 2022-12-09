import ftplib
import json
import os
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

from src.config.kcp_config import KCPConfig, KCPClientConfig
from src.handlers.kcp_interface import KCPHandler, GithubDownloadException
from src.helpers.ftp import FTPProcessor, FTPFile
from src.logger.bot_logger import BotLogger
from src.service.mode import ServiceMode


class CloudflareException(Exception):
    def __init__(self):
        super(CloudflareException, self).__init__()


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


class ApexHandler(KCPHandler):
    def __init__(self, bot_logger: BotLogger, svc_mode: ServiceMode, config: KCPConfig, panel_user: str, panel_passwd: str):
        super(ApexHandler, self).__init__(bot_logger, svc_mode, config)
        self._bot_logger: BotLogger = bot_logger
        self._kcp_file: Optional[str] = None
        self._config: KCPConfig = config
        self._panel_user: str = panel_user
        self._panel_passwd: str = panel_passwd
        self._url: str = "https://panel.apexminecrafthosting.com"
        self._login_url: str = f"{self._url}/site/login"
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

    def _login(self):
        r = requests.get(self._login_url, headers=self._default_headers)
        if r.status_code == 429:
            raise CloudflareException()
        soup = BeautifulSoup(r.text, "html.parser")
        token_input = soup.find("input", attrs={"type": "hidden", "name": "YII_CSRF_TOKEN"})
        if not token_input:
            raise TokenNotFoundException(f"Unable to find a valid token")
        self._csrf_token = token_input.get("value")
        self._cookies = r.cookies.copy()
        self._resolve_challenge(r)
        login_data: dict[str, str] = {
            "YII_CSRF_TOKEN": self._csrf_token,
            "LoginForm[name]": self._panel_user,
            "LoginForm[password]": self._panel_passwd,
            "LoginForm[rememberMe]": "1",
            "LoginForm[ignoreIp]": "1",
            "yt0": "Login"
        }
        self._default_headers.update({"Sec-Fetch-Site": "same-origin"})
        self._default_headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        self._default_headers.update({"Origin": "null"})
        cookie_capture = requests.post(self._login_url, headers=self._default_headers, data=login_data, cookies=self._cookies, allow_redirects=False)
        self._cookies.update(cookie_capture.cookies.copy())
        log = requests.post(self._login_url, headers=self._default_headers, data=login_data, cookies=self._cookies)
        self._default_headers.pop("Content-Type")
        self._default_headers.pop("Origin")
        self._cookies.update(log.cookies.copy())
        return log

    def _resolve_challenge(self, login_panel):
        s = BeautifulSoup(login_panel.text, "html.parser")
        challenge_id = ""
        for script in s.find_all("script"):
            challenge_id_find = re.search(r"r:\'([a-zA-Z0-9]+)\'", script.text)
            if not challenge_id_find:
                continue
            challenge_id = challenge_id_find.group(1)
        if not challenge_id:
            raise Exception
        challenge = f"{self._url}/cdn-cgi/challenge-platform/h/b/cv/result/{challenge_id}"
        r = requests.post(challenge, headers=self._default_headers, cookies=self._cookies)
        if r.status_code != 200:
            raise Exception
        self._cookies.update(r.cookies.copy())

    @classmethod
    def _get_server_url(cls, login_response) -> str:
        uri = re.search(r"/server/\d+", login_response.text)
        if not uri:
            raise ServerUrlNotFoundException("Unable to find a valid server url!")
        return uri.group(0)

    @classmethod
    def _get_redirect_url(cls, login_response) -> str:
        uri = re.search(r"/server/index/\d+", login_response.text)
        if not uri:
            raise ServerUrlNotFoundException("Unable to find a valid server url!")
        return uri.group(0)

    def _get_ftp_creds(self, login_response, server_id: str):
        ip_finder = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}", login_response.text)
        if not ip_finder:
            raise IPNotFoundException("")
        server_ip = ip_finder.group(0).split(":")[0]
        server_port = ip_finder.group(0).split(":")[1]
        ftp_port = "21"
        ftp_user = f"{self._panel_user.title()}.{server_id}"
        return server_ip, server_port, ftp_port, ftp_user

    def _do_redirect(self, url: str):
        r = requests.get(url, headers=self._default_headers, cookies=self._cookies)
        self._cookies.update(r.cookies)

    def _save_changes(self, login_response, jar_name: str) -> dict[str, str]:
        s = BeautifulSoup(login_response.text, "html.parser")
        location_selected = s.find("option", attrs={"data-transfer-type": "location", "selected": True}).get("data-location")
        server_name = s.find("input", attrs={"name": "Server[name]"}).get("value")
        server_players = s.find("input", attrs={"name": "Server[players]"}).get("value")
        server_domain = s.find("input", attrs={"name": "Server[domain]"}).get("value")
        world_name = s.find("input", attrs={"id": "world-name"}).get("value")
        kick_delay = s.find("input", attrs={"name": "Server[kick_delay]"}).get("value")
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

    def download_bin(self):
        # TODO this needs some cleanup :P
        dashboard = self._login()
        server_url: str = f"{self._url}{self._get_server_url(dashboard)}"
        redirect_server_url: str = f"{self._url}{self._get_redirect_url(dashboard)}"
        self._do_redirect(redirect_server_url)
        self._resolve_challenge(dashboard)
        server_id: str = server_url.split("/")[-1]
        self._default_headers.update({"Referer": f"{self._url}/server/{server_id}"})
        server_ip, server_port, ftp_port, ftp_user = self._get_ftp_creds(dashboard, server_id)
        url = "https://api.github.com/repos/BlackLotus-SMP/GOKCPJavaDeploy/releases"
        java_release_ver = "17"
        try:
            r = requests.get(url)
        except Exception as e:
            self._bot_logger.error(f"Unable to get valid KCP assets {e}")
            raise GithubDownloadException(f"Unable to get valid KCP assets {e}")
        if r.status_code != 200:
            raise GithubDownloadException(f"Unable to get a valid release, got status code {r.status_code}!")
        download_url = ""
        for release in r.json():
            if release.get("name") == f"java-{java_release_ver}":
                download_url = release.get("assets")[0].get("browser_download_url")
                break
        if not download_url:
            raise GithubDownloadException(f"Unable to get valid KCP assets")

        local_resources: str = "resources"
        jar_name: str = "apex_java"
        if not os.path.isdir(local_resources):
            os.mkdir(local_resources)
        if os.path.isfile(f"{local_resources}/{jar_name}-{java_release_ver}.jar"):
            os.remove(f"{local_resources}/{jar_name}-{java_release_ver}.jar")

        kcp_jar = requests.get(download_url, stream=True)
        with open(f"{local_resources}/{jar_name}-{java_release_ver}.jar", "wb") as f:
            for chunk in kcp_jar.iter_content(chunk_size=2048):
                if chunk:
                    f.write(chunk)

        with ftplib.FTP(host=server_ip, user=ftp_user, passwd=self._panel_passwd) as ftp:
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
                ftp_processor.create_dir("jar")
            if not data_dir_found:
                ftp_processor.create_dir("data")

            data_files: list[FTPFile] = ftp_processor.list_files("data")
            config_dir_found: bool = False
            for f in data_files:
                if f.is_dir() and f.get_name() == "config":
                    config_dir_found: bool = True

            if not config_dir_found:
                ftp_processor.create_dir("config", base_path="data")

            config_files: list[FTPFile] = ftp_processor.list_files("data/config")
            config_file_found: bool = False
            for f in config_files:
                if not f.is_dir() and f.get_name() == "config.json":
                    config_file_found: bool = True
            if config_file_found:
                ftp_processor.delete_file("data/config/config.json")

            jar_files: list[FTPFile] = ftp_processor.list_files("jar")
            jar_found: bool = False
            for f in jar_files:
                if not f.is_dir() and f.get_name() == f"{jar_name}-{java_release_ver}.jar":
                    jar_found: bool = True
            if jar_found:
                ftp_processor.delete_file(f"jar/{jar_name}-{java_release_ver}.jar")

            config: dict[str, str] = {
                "remoteaddr": self._config.remote,
                "localaddr": self._config.listen,
                "mode": self._config.mode,
                "crypt": self._config.crypt,
                "key": self._config.key
            }
            with open(f"{local_resources}/config.json", "w") as f:
                f.write(json.dumps(config, indent=2))

            ftp_processor.upload_file(
                f"{local_resources}/{jar_name}-{java_release_ver}.jar",
                f"{jar_name}-{java_release_ver}.jar",
                "jar"
            )
            ftp_processor.upload_file(f"{local_resources}/config.json", "config.json", "data/config")
            os.remove(f"{local_resources}/config.json")
        os.remove(f"{local_resources}/{jar_name}-{java_release_ver}.jar")

        apply_changes: dict[str, str] = self._save_changes(dashboard, f"{jar_name}-{java_release_ver}.jar")
        applied = requests.post(server_url, headers=self._default_headers, data=apply_changes, cookies=self._cookies)
        if applied.status_code != 200:
            raise Exception

    def run_kcp(self):
        pass
