import json
from pathlib import Path
from typing import Final

MANIFEST_PATH = Path(__file__).parent / "manifest.json"
with open(MANIFEST_PATH, encoding="utf-8") as f:
    INTEGRATION_VERSION: Final[str] = json.load(f).get("version", "0.0.0")


DOMAIN:Final[str] = "recalbox"
URL_BASE:Final[str] = "/recalbox"

JSMODULES = [
    {
        "name": "Recalbox Card",
        "filename": "recalbox-card.js",
        "version": INTEGRATION_VERSION,
    },
]