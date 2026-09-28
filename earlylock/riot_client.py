import base64
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import requests


class LockfileError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LockfileCredentials:
    name: str
    pid: int
    port: int
    password: str
    protocol: str


def default_lockfile_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise LockfileError("LOCALAPPDATA 환경 변수를 찾을 수 없습니다.")

    return Path(local_app_data) / "Riot Games" / "Riot Client" / "Config" / "lockfile"


def read_lockfile(path: Path | None = None) -> LockfileCredentials:
    lockfile_path = path or default_lockfile_path()

    try:
        fields = lockfile_path.read_text(encoding="utf-8").strip().split(":")
    except FileNotFoundError as error:
        raise LockfileError(
            "Riot lockfile을 찾을 수 없습니다. VALORANT가 실행 중인지 확인해 주세요."
        ) from error
    except OSError as error:
        raise LockfileError(f"Riot lockfile을 읽을 수 없습니다: {error}") from error

    if len(fields) != 5:
        raise LockfileError("Riot lockfile 형식이 올바르지 않습니다.")

    name, pid, port, password, protocol = fields
    try:
        return LockfileCredentials(
            name=name,
            pid=int(pid),
            port=int(port),
            password=password,
            protocol=protocol,
        )
    except ValueError as error:
        raise LockfileError("Riot lockfile의 PID 또는 포트가 올바르지 않습니다.") from error


class EndpointType(str, Enum):
    LOCAL = "local"
    PD = "pd"
    GLZ = "glz"
    SHARED = "shared"


class RiotClient:
    DEFAULT_TIMEOUT = (3.05, 10.0)
    VERSION_URL = "https://valorant-api.com/v1/version"
    CLIENT_PLATFORM = (
        "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjog"
        "IldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5"
        "MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVu"
        "a25vd24iDQp9"
    )

    def __init__(
        self,
        region: str = "kr",
        *,
        credentials: LockfileCredentials | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self._region = region
        self._shard = region
        self._session = session or requests.Session()
        self._credentials = credentials or read_lockfile()

        self._local_headers = self._build_local_headers()
        self._base_urls = self._build_base_urls()

        entitlements = self._get_entitlements()
        self.puuid = entitlements["subject"]
        self._remote_headers = self._build_remote_headers(entitlements)

        chat_session = self.fetch("/chat/v1/session", EndpointType.LOCAL)
        self.player_name = chat_session["game_name"]
        self.player_tag = chat_session["game_tag"]

    @property
    def port(self) -> int:
        return self._credentials.port

    def _build_local_headers(self) -> dict[str, str]:
        token = base64.b64encode(
            f"riot:{self._credentials.password}".encode("utf-8")
        ).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _get_entitlements(self) -> dict[str, Any]:
        response = self._session.get(
            f"{self._credentials.protocol}://127.0.0.1:{self.port}/entitlements/v1/token",
            headers=self._local_headers,
            verify=False,
            timeout=self.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def _build_remote_headers(self, entitlements: dict[str, Any]) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {entitlements['accessToken']}",
            "X-Riot-Entitlements-JWT": entitlements["token"],
            "X-Riot-ClientPlatform": self.CLIENT_PLATFORM,
            "X-Riot-ClientVersion": self._get_current_version(),
        }

    def _get_current_version(self) -> str:
        response = self._session.get(
            self.VERSION_URL,
            timeout=self.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()["data"]
        version_number = data["version"].split(".")[3]
        return f"{data['branch']}-shipping-{data['buildVersion']}-{version_number}"

    def _build_base_urls(self) -> dict[EndpointType, str]:
        return {
            EndpointType.LOCAL: (
                f"{self._credentials.protocol}://127.0.0.1:{self.port}"
            ),
            EndpointType.PD: f"https://pd.{self._shard}.a.pvp.net",
            EndpointType.GLZ: (
                f"https://glz-{self._region}-1.{self._shard}.a.pvp.net"
            ),
            EndpointType.SHARED: f"https://shared.{self._shard}.a.pvp.net",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        endpoint_type: EndpointType,
        json_data: dict[str, Any] | list[str] | None = None,
    ) -> Any:
        try:
            endpoint_type = EndpointType(endpoint_type)
        except ValueError as error:
            raise ValueError(f"지원하지 않는 endpoint type입니다: {endpoint_type}") from error

        is_local = endpoint_type is EndpointType.LOCAL
        response = self._session.request(
            method,
            f"{self._base_urls[endpoint_type]}{endpoint}",
            headers=self._local_headers if is_local else self._remote_headers,
            json=json_data,
            verify=not is_local,
            timeout=self.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    def fetch(
        self,
        endpoint: str,
        endpoint_type: EndpointType,
    ) -> dict[str, Any]:
        payload = self._request("GET", endpoint, endpoint_type)
        if not isinstance(payload, dict):
            raise TypeError("GET 응답이 JSON object 형식이 아닙니다.")
        return payload

    def post(
        self,
        endpoint: str,
        endpoint_type: EndpointType,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self._request("POST", endpoint, endpoint_type, json_data)
        if not isinstance(payload, dict):
            raise TypeError("POST 응답이 JSON object 형식이 아닙니다.")
        return payload

    def put(
        self,
        endpoint: str,
        endpoint_type: EndpointType,
        json_data: dict[str, Any] | list[str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        return self._request("PUT", endpoint, endpoint_type, json_data)

    def close(self) -> None:
        self._session.close()
