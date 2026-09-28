import os
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class ValorantNameService:
    CLIENT_PLATFORM = (
        "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0K"
        "CSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0K"
        "CSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4w"
        "LjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxh"
        "dGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9"
    )

    AUTH_URL = (
        "https://auth.riotgames.com/authorize"
        "?redirect_uri=https%3A%2F%2Fplayvalorant.com%2Fopt_in"
        "&client_id=play-valorant-web-prod"
        "&response_type=token%20id_token"
        "&nonce=1"
        "&scope=account%20openid"
    )

    ENTITLEMENT_URL = (
        "https://entitlements.auth.riotgames.com/api/token/v1"
    )

    VERSION_URL = "https://valorant-api.com/v1/version"

    NAME_SERVICE_URL = (
        "https://pd.kr.a.pvp.net/name-service/v2/players"
    )

    def __init__(self, ssid: str | None = None) -> None:
        self._ssid = (
            ssid
            or dotenv_values(ENV_PATH, encoding="utf-8-sig", interpolate=False).get("RIOT_SSID")
            or os.environ.get("RIOT_SSID", "")
        ).strip()
        if not self._ssid:
            raise RuntimeError("프로젝트 루트의 .env 파일에 RIOT_SSID를 입력해 주세요.")

        self._access_token = self._get_access_token()
        self._entitlement_token = self._get_entitlement_token()
        self._client_version = self._get_client_version()

    def get_player_names(
        self,
        puuids: Iterable[str],
    ) -> dict[str, tuple[str, str]]:
        puuids = list(dict.fromkeys(puuid for puuid in puuids if puuid))
        if not puuids:
            return {}

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "X-Riot-Entitlements-JWT": self._entitlement_token,
            "X-Riot-ClientPlatform": self.CLIENT_PLATFORM,
            "X-Riot-ClientVersion": self._client_version,
        }

        response = requests.put(
            self.NAME_SERVICE_URL,
            headers=headers,
            json=puuids,
            timeout=10,
        )

        response.raise_for_status()

        players = response.json()
        if not isinstance(players, list):
            raise ValueError("이름 조회 응답이 JSON array 형식이 아닙니다.")

        return {
            player["Subject"]: (
                player["GameName"],
                player["TagLine"],
            )
            for player in players
            if isinstance(player, dict)
            and player.get("Subject") in puuids
            and isinstance(player.get("GameName"), str)
            and player["GameName"]
            and isinstance(player.get("TagLine"), str)
            and player["TagLine"]
        }

    def _get_access_token(self) -> str:
        response = requests.get(
            self.AUTH_URL,
            cookies={
                "ssid": self._ssid,
            },
            allow_redirects=False,
            timeout=10,
        )

        response.raise_for_status()

        location = response.headers.get("Location", "")

        fragment = urlparse(location).fragment
        params = parse_qs(fragment)

        if "access_token" not in params:
            raise RuntimeError("Riot 로그인이 필요합니다.")

        return params["access_token"][0]

    def _get_entitlement_token(self) -> str:
        response = requests.post(
            self.ENTITLEMENT_URL,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
            json={},
            timeout=10,
        )

        response.raise_for_status()

        return response.json()["entitlements_token"]

    def _get_client_version(self) -> str:
        response = requests.get(
            self.VERSION_URL,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()["data"]["riotClientVersion"]
