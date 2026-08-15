import os

class Client:
    def __init__(self, region: str="kr"):
        self.region = region
        self.lockfile_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Riot Games\Riot Client\Config\lockfile")

        lockfile = self.__get_lock_file()
        self.name = lockfile["name"]
        self.PID = lockfile["PID"]
        self.port = lockfile["port"]
        self.password = lockfile["password"]
        self.protocol = lockfile["protocol"]

    def __get_lock_file(self) -> dict[str, str]:
        try:
            with open(self.lockfile_path) as lockfile:
                data = lockfile.read().split(":")
                keys = ["name", "PID", "port", "password", "protocol"]
                return dict(zip(keys, data))
        except FileNotFoundError:
            raise RuntimeError("can't find lockfile")