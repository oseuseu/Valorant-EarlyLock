import os
from dataclasses import dataclass
from pathlib import Path


class LockfileError(RuntimeError):
    pass


@dataclass(frozen=True)
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
