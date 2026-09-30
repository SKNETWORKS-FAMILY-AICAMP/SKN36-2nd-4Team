"""대시보드 스냅샷을 프로세스당 한 번만 읽는다."""

import json
from pathlib import Path

_PAYLOAD: dict | None = None


def get_dashboard_payload() -> dict:
    """core_dashboard.json을 메모리에 올린 뒤 같은 객체를 반환한다."""
    global _PAYLOAD
    if _PAYLOAD is None:
        path = Path(__file__).resolve().parents[1] / "data" / "core_dashboard.json"
        if not path.is_file():
            _PAYLOAD = {}
        else:
            _PAYLOAD = json.loads(path.read_text(encoding="utf-8"))
    return _PAYLOAD
