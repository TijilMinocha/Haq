from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_CONFIG_DIR = Path(__file__).parent
CURRENT_FY = "2026_27"


@lru_cache
def load_config(fy: str = CURRENT_FY) -> dict[str, Any]:
    with (_CONFIG_DIR / f"fy{fy}.yaml").open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data
