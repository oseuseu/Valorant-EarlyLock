import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from earlylock.name_finder import ValorantNameService


def response(payload=None, *, headers=None):
    result = Mock()
    result.json.return_value = payload
    result.headers = headers or {}
    return result


class ValorantNameServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory())
        self.env_path = Path(directory) / ".env"
        self.enterContext(patch("earlylock.name_finder.ENV_PATH", self.env_path))
        self.get = self.enterContext(patch("earlylock.name_finder.requests.get"))
        self.post = self.enterContext(patch("earlylock.name_finder.requests.post"))
        self.put = self.enterContext(patch("earlylock.name_finder.requests.put"))
        self.get.side_effect = [
            response(headers={
                "Location": "https://playvalorant.com/opt_in#access_token=test-web-token",
            }),
            response({"data": {"riotClientVersion": "test-version"}}),
        ]
        self.post.return_value = response({"entitlements_token": "test-entitlement"})

    def test_uses_web_authentication_for_all_requested_puuids(self) -> None:
        self.put.return_value = response([
            {"Subject": "hidden", "GameName": "HiddenPlayer", "TagLine": "KR1"},
            {"Subject": "visible", "GameName": "VisiblePlayer", "TagLine": "KR2"},
        ])
        service = ValorantNameService("test-ssid")

        names = service.get_player_names(iter(["hidden", "visible", "hidden", ""]))

        self.assertEqual(names, {
            "hidden": ("HiddenPlayer", "KR1"),
            "visible": ("VisiblePlayer", "KR2"),
        })
        self.assertEqual(self.get.call_args_list[0].args, (service.AUTH_URL,))
        self.assertEqual(self.get.call_args_list[0].kwargs["cookies"], {"ssid": "test-ssid"})
        self.assertFalse(self.get.call_args_list[0].kwargs["allow_redirects"])
        self.assertEqual(self.put.call_args.args, (service.NAME_SERVICE_URL,))
        self.assertEqual(self.put.call_args.kwargs["json"], ["hidden", "visible"])
        self.assertEqual(self.put.call_args.kwargs["headers"]["Authorization"], "Bearer test-web-token")
        self.assertEqual(self.put.call_args.kwargs["headers"]["X-Riot-Entitlements-JWT"], "test-entitlement")
        self.assertEqual(self.put.call_args.kwargs["headers"]["X-Riot-ClientVersion"], "test-version")

    def test_empty_lookup_does_not_send_request(self) -> None:
        service = ValorantNameService("test-ssid")
        self.assertEqual(service.get_player_names([""]), {})
        self.put.assert_not_called()

    def test_skips_incomplete_or_unrequested_players(self) -> None:
        self.put.return_value = response([
            None,
            {"Subject": "valid", "GameName": "Player", "TagLine": "KR1"},
            {"Subject": "blank", "GameName": "", "TagLine": ""},
            {"Subject": "partial", "GameName": "Player"},
            {"Subject": "unrequested", "GameName": "Other", "TagLine": "KR2"},
        ])
        service = ValorantNameService("test-ssid")
        self.assertEqual(
            service.get_player_names(["valid", "blank", "partial"]),
            {"valid": ("Player", "KR1")},
        )

    def test_reads_ssid_from_environment(self) -> None:
        with patch.dict("os.environ", {"RIOT_SSID": "environment-ssid"}):
            ValorantNameService()
        self.assertEqual(
            self.get.call_args_list[0].kwargs["cookies"],
            {"ssid": "environment-ssid"},
        )

    def test_reads_dotenv_before_environment_without_expanding_cookie(self) -> None:
        self.env_path.write_text(
            '# Riot session\nRIOT_SSID="file-${COOKIE}-ssid"\n',
            encoding="utf-8-sig",
        )
        with patch.dict("os.environ", {"RIOT_SSID": "environment-ssid"}):
            ValorantNameService()
        self.assertEqual(
            self.get.call_args_list[0].kwargs["cookies"],
            {"ssid": "file-${COOKIE}-ssid"},
        )

    def test_missing_ssid_fails_before_network_access(self) -> None:
        self.env_path.write_text("RIOT_SSID=\n", encoding="utf-8")
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "RIOT_SSID"):
                ValorantNameService()
        self.get.assert_not_called()

    def test_requires_login_if_redirect_contains_no_access_token(self) -> None:
        self.get.side_effect = [response(headers={"Location": "https://auth.riotgames.com/login"})]
        with self.assertRaises(RuntimeError):
            ValorantNameService("expired-ssid")
        self.post.assert_not_called()

    def test_rejects_unexpected_response_shape(self) -> None:
        self.put.return_value = response({"error": "unexpected"})
        service = ValorantNameService("test-ssid")
        with self.assertRaises(ValueError):
            service.get_player_names(["player"])


if __name__ == "__main__":
    unittest.main()
