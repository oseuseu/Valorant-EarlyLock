from client import Client
from constants import Agent

class ValorantAPI:
    def __init__(self, client: Client):
        self.client = client

    def get_pregame_match(self, id: str) -> dict | None:
        try:
            return self.client.fetch(endpoint=f"/pregame/v1/matches/{id}", endpoint_type="glz")
        except:
            return None

    def get_pregame_player(self) -> dict | None:
        try:
            puuid = self.client.puuid
            return self.client.fetch(endpoint=f"/pregame/v1/players/{puuid}", endpoint_type="glz")
        except:
            return None

    def get_pregame_id(self) -> str | None:
        try:
            return self.get_pregame_player()["MatchID"]
        except:
            return None

    def select_agent(self, match_id: str, agent: Agent):
        self.client.post(endpoint=f"/pregame/v1/matches/{match_id}/select/{agent.uuid}", endpoint_type="glz")

    def lock_agent(self, match_id: str, agent: Agent):
            self.client.post(endpoint=f"/pregame/v1/matches/{match_id}/lock/{agent.uuid}", endpoint_type="glz")
        