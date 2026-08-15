import os
import base64
import requests
import json

class Client:
    def __init__(self, region: str="kr"):
        self.region = region
        self.shard = region

        lockfile_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Riot Games\Riot Client\Config\lockfile")
        lockfile = self.__get_lock_file(lockfile_path)

        self.name = lockfile["name"]
        self.PID = lockfile["PID"]
        self.port = lockfile["port"]
        self.password = lockfile["password"]
        self.protocol = lockfile["protocol"]

        self.local_headers = self.__get_local_headers()

        entitlements = self.__get_entitlements()
        self.puuid = entitlements["subject"]
        self.remote_headers = self.__get_remote_headers(entitlements)

        self.__set_base_urls()

        session = self.rnet_fetch_chat_session()
        self.player_name = session["game_name"]
        self.player_tag = session["game_tag"]

    def __get_lock_file(self, path: str) -> dict[str, str]:
        try:
            with open(path) as lockfile:
                data = lockfile.read().split(":")
                keys = ["name", "PID", "port", "password", "protocol"]
                return dict(zip(keys, data))
        except FileNotFoundError:
            raise RuntimeError("can't find lockfile")

    def __get_local_headers(self) -> dict[str, str]:
        auth = base64.b64encode(
            f"riot:{self.password}".encode()
        ).decode()

        return {
            "Authorization": f"Basic {auth}"
        }

    def __get_entitlements(self) -> dict:
        response = requests.get(
            f"https://127.0.0.1:{self.port}/entitlements/v1/token",
            headers=self.local_headers,
            verify=False,
        )
        return response.json()

    def __get_remote_headers(self, entitlements: dict) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {entitlements['accessToken']}",
            "X-Riot-Entitlements-JWT": entitlements["token"],
            "X-Riot-ClientPlatform": "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9",
            "X-Riot-ClientVersion": self.__get_current_version(),
        }

    def __get_current_version(self) -> str:
        data = requests.get("https://valorant-api.com/v1/version")
        data = data.json()["data"]
        return f"{data['branch']}-shipping-{data['buildVersion']}-{data['version'].split('.')[3]}"

    def __set_base_urls(self) -> None:
        self.base_url = f"https://pd.{self.shard}.a.pvp.net"
        self.base_url_glz = f"https://glz-{self.region}-1.{self.shard}.a.pvp.net"
        self.base_url_shared = f"https://shared.{self.shard}.a.pvp.net"

    def rnet_fetch_chat_session(self) -> dict[str, str]:
        data = self.fetch(endpoint="/chat/v1/session", endpoint_type="local")
        return data
    
    def fetch(self, endpoint, endpoint_type) -> dict:
        if endpoint_type == "local":
            response = requests.get(f"https://127.0.0.1:{self.port}{endpoint}", headers=self.local_headers, verify=False)
        elif endpoint_type in ["pd", "glz", "shared"]:
            if endpoint_type == "glz":
                url = self.base_url_glz
            elif endpoint_type == "shared":
                url = self.base_url_shared
            else:
                url = self.base_url
            response = requests.get(f'{url}{endpoint}', headers=self.remote_headers)
        else:
            raise ValueError("wrong endpoint_type")

        response.raise_for_status()
        return response.json()

    def post(self, endpoint, endpoint_type, json_data={}) -> dict:
        url = self.base_url_glz if endpoint_type == "glz" else self.base_url
        response = requests.post(f"{url}{endpoint}", headers=self.remote_headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint, endpoint_type, json_data={}) -> dict:
        url = self.base_url_glz if endpoint_type == "glz" else self.base_url
        response = requests.put(f"{url}{endpoint}", headers=self.remote_headers, json=json_data)
        response.raise_for_status()
        return response.json()
