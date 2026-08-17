from client import Client
from constants import Agent, GameState

class ValorantAPI:
    def __init__(self, client: Client):
        self.client = client

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

    def get_pregame_match(self, id: str) -> dict | None:
        try:
            return self.client.fetch(endpoint=f"/pregame/v1/matches/{id}", endpoint_type="glz")
        except:
            return None

    def get_coregame_player(self) -> dict | None:
        try:
            puuid = self.client.puuid
            return self.client.fetch(endpoint=f"/core-game/v1/players/{puuid}", endpoint_type="glz")
        except:
            return None

    def get_coregame_id(self) -> str | None:
        try:
            return self.get_coregame_player()["MatchID"]
        except:
            return None

    def get_coregame_match(self, id: str) -> dict | None:
        try:
            return self.client.fetch(endpoint=f"/core-game/v1/matches/{id}", endpoint_type="glz")
        except:
            return None

    def is_pregame(self) -> bool:
        return self.get_pregame_player() != None

    def is_coregame(self) -> bool:
        return self.get_coregame_player() != None

    def get_game_state(self) -> GameState:
        if self.is_pregame() == True:
            return GameState.PREGAME
        if self.is_coregame() == True:
            return GameState.IN_GAME
        return GameState.LOBBY

    def select_agent(self, match_id: str, agent: Agent) -> bool:
        try:
            self.client.post(endpoint=f"/pregame/v1/matches/{match_id}/select/{agent.uuid}", endpoint_type="glz")
            return True
        except:
            return False

    def lock_agent(self, match_id: str, agent: Agent) -> bool:
        try:
            self.client.post(endpoint=f"/pregame/v1/matches/{match_id}/lock/{agent.uuid}", endpoint_type="glz")
            return True
        except:
            return False
        