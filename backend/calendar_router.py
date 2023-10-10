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

def _write_cache(year: str, lang: str, data: dict):
    try:
        p = _cache_path(year, lang)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")

def _parse_arabic_date(date_str: str):
    if not date_str or date_str.strip() == '-':
        return None
    date_str = date_str.strip()
    arabic_months = {
        'يناير': 'January', 'فبراير': 'February', 'مارس': 'March',
        'أبريل': 'April', 'مايو': 'May', 'يونيو': 'June',
        'يوليو': 'July', 'أغسطس': 'August', 'سبتمبر': 'September',
        'أكتوبر': 'October', 'نوفمبر': 'November', 'ديسمبر': 'December',
    }
    for ar, en in arabic_months.items():
        date_str = date_str.replace(ar, en)
    for fmt in ('%d %B %Y', '%j %B %Y', '%d %b %Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def _calc_status(start_str: str, end_str: str, lang: str) -> str:
    now = datetime.now()
    start = _parse_arabic_date(start_str)
    end = _parse_arabic_date(end_str)

    if not start and not end:
        return 'غير محدد' if lang == 'ar' else 'Not specified'
    if start and not end:
        return ('قريباً' if lang == 'ar' else 'Coming Soon') if now < start else ('متاح' if lang == 'ar' else 'Available')
    if end and not start:
        return ('متاح' if lang == 'ar' else 'Available') if now <= end else ('مغلق' if lang == 'ar' else 'Closed')
    if now < start:
        return 'قريباً' if lang == 'ar' else 'Coming Soon'
    elif now <= end:
        return 'متاح' if lang == 'ar' else 'Available'
    return 'مغلق' if lang == 'ar' else 'Closed'
