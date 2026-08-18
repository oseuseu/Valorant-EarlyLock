from earlylock.infrastructure.riot.api import ValorantApi
from earlylock.infrastructure.riot.client import RiotClient
import earlylock.infrastructure.riot.lockfile as lockfile


lock = lockfile.read_lockfile()
client = RiotClient(region="kr", credentials=lock)
api = ValorantApi(client)

id = api.get_coregame_id()
match = api.get_coregame_match(id)

print(match)