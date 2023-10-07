import os
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter(tags=["calendar"])

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DURATION = 3600

def _cache_path(year: str, lang: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"calendar_{year}_{lang}.json"

def _read_cache(year: str, lang: str):
    p = _cache_path(year, lang)
    if p.exists() and (datetime.now().timestamp() - p.stat().st_mtime) < CACHE_DURATION:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None
