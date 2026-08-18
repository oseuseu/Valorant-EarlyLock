import base64
from enum import Enum
from typing import Any

import requests

from earlylock.infrastructure.riot.lockfile import (
    LockfileCredentials,
    read_lockfile,
)


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
        self.region = region
        self.shard = region
        self._session = session or requests.Session()
        self._credentials = credentials or read_lockfile()

        self.local_headers = self._build_local_headers()
        self._set_base_urls()

        entitlements = self._get_entitlements()
        self.puuid = entitlements["subject"]
        self.remote_headers = self._build_remote_headers(entitlements)

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
            headers=self.local_headers,
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

    def _set_base_urls(self) -> None:
        self._base_urls = {
            EndpointType.LOCAL: (
                f"{self._credentials.protocol}://127.0.0.1:{self.port}"
            ),
            EndpointType.PD: f"https://pd.{self.shard}.a.pvp.net",
            EndpointType.GLZ: (
                f"https://glz-{self.region}-1.{self.shard}.a.pvp.net"
            ),
            EndpointType.SHARED: f"https://shared.{self.shard}.a.pvp.net",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        endpoint_type: EndpointType,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            endpoint_type = EndpointType(endpoint_type)
        except ValueError as error:
            raise ValueError(f"지원하지 않는 endpoint type입니다: {endpoint_type}") from error

        is_local = endpoint_type is EndpointType.LOCAL
        response = self._session.request(
            method,
            f"{self._base_urls[endpoint_type]}{endpoint}",
            headers=self.local_headers if is_local else self.remote_headers,
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
        return self._request("GET", endpoint, endpoint_type)

    def post(
        self,
        endpoint: str,
        endpoint_type: EndpointType,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("POST", endpoint, endpoint_type, json_data)

    def put(
        self,
        endpoint: str,
        endpoint_type: EndpointType,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request("PUT", endpoint, endpoint_type, json_data)

    def close(self) -> None:
        self._session.close()
