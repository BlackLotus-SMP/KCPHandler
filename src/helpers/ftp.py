import ftplib


class FTPFile:
    def __init__(self, name: str, is_dir: str):
        self._name: str = name
        self._dir: bool = is_dir.lower() == "d"

    def is_dir(self) -> bool:
        return self._dir

    def get_name(self) -> str:
        return self._name

    def __repr__(self):
        return f"File[name={self.get_name()}, dir={self.is_dir()}]"


class FTPProcessor:
    def __init__(self, ftp: ftplib.FTP):
        self._ftp: ftplib.FTP = ftp

    @classmethod
    def get_files(cls, file_list: list[str]) -> list[FTPFile]:
        parsed_file_list: list[FTPFile] = []
        for f in file_list:
            parsed: list[str] = [line for line in f.split(" ") if line]
            parsed_file_list.append(FTPFile(parsed[-1], parsed[0][0]))
        return parsed_file_list

    def create_dir(self, dir_: str):
        self._ftp.mkd(dir_)

    def delete_file(self, file_path: str):
        self._ftp.delete(file_path)

    def upload_file(self, file_path: str, file_name: str, remote_dir: str = ""):
        if not remote_dir:
            remote_dir = "/"
        self._ftp.cwd(remote_dir)
        self._ftp.storbinary(f"STOR {file_name}", open(file_path, "rb"))
        self._ftp.cwd("/")

    def list_files(self, dir_: str = "") -> list[FTPFile]:
        data: list = []
        if not dir_:
            dir_ = "/"
        self._ftp.cwd(dir_)
        self._ftp.dir(data.append)
        self._ftp.cwd("/")
        return self.get_files(data)
