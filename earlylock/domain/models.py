from dataclasses import dataclass
from enum import Enum


class GameState(Enum):
    LOBBY = "lobby"
    PREGAME = "pregame"
    IN_GAME = "in_game"

class Agent(Enum):
    GEKKO = ("게코", "e370fa57-4757-3604-3648-499e1f642d3f")
    FADE = ("페이드", "dade69b4-4f5a-8528-247b-219e5a1facd6")
    BREACH = ("브리치", "5f8d3a7f-467b-97f3-062c-13acf203c006")
    DEADLOCK = ("데드록", "cc8b64c8-4b25-4ff9-6e7f-37b4da43d235")
    TEJO = ("테호", "b444168c-4e35-8076-db47-ef9bf368f384")
    RAZE = ("레이즈", "f94c3b30-42be-e959-889c-5aa313dba261")
    CHAMBER = ("체임버", "22697a3d-45bf-8dd7-4fec-84a9e28c69d7")
    KAYO = ("케이/오", "601dbbe7-43ce-be57-2a40-4abd24953621")
    SKYE = ("스카이", "6f2a04ca-43e0-be17-7f36-b3908627744d")
    CYPHER = ("사이퍼", "117ed9e3-49f3-6512-3ccf-0cada7e3823b")
    SOVA = ("소바", "320b2a48-4d9b-a075-30f1-1f93a9b638fa")
    MIKS = ("믹스", "7c8a4701-4de6-9355-b254-e09bc2a34b72")
    KILLJOY = ("킬조이", "1e58de9c-4950-5125-93e9-a0aee9f98746")
    HARBOR = ("하버", "95b78ed7-4637-86d9-7e41-71ba8c293152")
    VYSE = ("바이스", "efba5359-4016-a1e5-7626-b1ae76895940")
    VIPER = ("바이퍼", "707eab51-4836-f488-046a-cda6bf494859")
    PHOENIX = ("피닉스", "eb93336a-449b-9c1b-0a54-a891f7921d69")
    VETO = ("비토", "92eeef5d-43b5-1d4a-8d03-b3927a09034b")
    ASTRA = ("아스트라", "41fb69c1-4189-7b37-f117-bcaf1e96f1bf")
    BRIMSTONE = ("브림스톤", "9f0d8ba9-4140-b941-57d3-a7ad57c6b417")
    ISO = ("아이소", "0e38b510-41a8-5780-5e8f-568b2a4f2d6c")
    CLOVE = ("클로브", "1dbf2edd-4729-0984-3115-daa5eed44993")
    NEON = ("네온", "bb2a4828-46eb-8cd1-e765-15848195d751")
    YORU = ("요루", "7f94d92c-4234-0a36-9646-3a87eb8b5c89")
    WAYLAY = ("웨이레이", "df1cb487-4902-002e-5c17-d28e83e78588")
    SAGE = ("세이지", "569fdd95-4d10-43ab-ca70-79becc718b46")
    REYNA = ("레이나", "a3bfb853-43b2-7238-a4f1-ad90e9e46bcc")
    OMEN = ("오멘", "8e253930-4c05-31dd-1b6c-968525494517")
    JETT = ("제트", "add6443a-41bd-e414-f6ad-e58d267f4e95")

    def __init__(self, display_name: str, uuid: str):
        self.display_name = display_name
        self.uuid = uuid


@dataclass(frozen=True)
class AutoPickSettings:
    agent: Agent
    pick_only: bool
    pick_delay_seconds: float = 6.0


@dataclass(frozen=True)
class PlayerName:
    puuid: str
    name: str
    tag: str


@dataclass(frozen=True)
class PlayerSnapshot:
    puuid: str
    name: str | None
    tag: str | None

    team: str | None
    agent: Agent | None
    is_lock: bool = False


@dataclass(frozen=True)
class MatchSnapshot:
    state: GameState
    match_id: str | None
    players: tuple[PlayerSnapshot, ...]

    @property
    def is_active(self) -> bool:
        return self.match_id is not None
