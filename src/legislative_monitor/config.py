from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    db_path: Path
    downloads_dir: Path
    topics_path: Path
    timeout_seconds: int
    max_retries: int
    page_size: int
    lookback_days: int
    google_service_account_file: str | None
    google_drive_root_folder_id: str | None
    google_sheet_id: str | None
    captcha_token: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path.cwd()
        return cls(
            db_path=root / os.getenv("MONITOR_DB_PATH", "data/monitor.sqlite3"),
            downloads_dir=root / os.getenv("MONITOR_DOWNLOAD_DIR", "downloads"),
            topics_path=root / os.getenv("MONITOR_TOPICS_PATH", "config/topics.json"),
            timeout_seconds=int(os.getenv("MONITOR_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("MONITOR_MAX_RETRIES", "3")),
            page_size=int(os.getenv("MONITOR_PAGE_SIZE", "50")),
            lookback_days=int(os.getenv("MONITOR_LOOKBACK_DAYS", "7")),
            google_service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
            google_drive_root_folder_id=os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID") or None,
            google_sheet_id=os.getenv("GOOGLE_SHEET_ID") or None,
            captcha_token=os.getenv("CONGRESO_CAPTCHA_TOKEN") or None,
        )


def load_topics(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data.get("topics"), list):
        raise ValueError("topics.json debe contener una lista 'topics'.")
    return data
