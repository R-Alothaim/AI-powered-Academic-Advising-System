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
MAX_RETRIES = 3

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

async def _fetch_calendar(year: str, lang: str) -> dict:
    cached = _read_cache(year, lang)
    if cached:
        return cached

    empty = {'bachelor_s1': [], 'bachelor_s2': [], 'graduate_s1': [], 'graduate_s2': []}
    url = f"https://university.edu.sa/{lang}/academic-calendar/{year}/"

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}")
            html = resp.text
    except Exception as e:
        logger.warning(f"Calendar fetch failed: {e}")
        old = _read_cache(year, lang)
        return old if old else empty

    try:
        data = _parse_calendar_html(html, lang)
        _write_cache(year, lang, data)
        return data
    except Exception as e:
        logger.error(f"Calendar parse failed: {e}")
        return empty

def _parse_calendar_html(html: str, lang: str) -> dict:
    data = {'bachelor_s1': [], 'bachelor_s2': [], 'graduate_s1': [], 'graduate_s2': []}

    sections = {
        'bachelor': re.search(r'id=["\']bachelor-content["\'].*?(?=id=["\']graduate-content|$)', html, re.DOTALL),
        'graduate': re.search(r'id=["\']graduate-content["\'].*?$', html, re.DOTALL),
    }

    for section_key, match in sections.items():
        if not match:
            continue
        section_html = match.group(0)

        for sem_idx in range(2):
            collapse_id = f"{section_key}-semester-{sem_idx}-collapse"
            collapse_match = re.search(
                rf'id=["\']{ re.escape(collapse_id) }["\'].*?accordion-body.*?>(.*?)</div>\s*</div>\s*</div>',
                section_html, re.DOTALL
            )
            if not collapse_match:
                continue

            body = collapse_match.group(1)
            cards = re.findall(r'class=["\'][^"\']*entry-card[^"\']*["\'].*?(?=class=["\'][^"\']*entry-card|$)', body, re.DOTALL)

            events = []
            for card in cards:
                if 'no-data-card' in card or 'status-summary' in card:
                    continue
                title_m = re.search(r'nds-card-title["\']?>([^<]+)', card)
                if not title_m:
                    continue
                title = title_m.group(1).strip()
                if not title:
                    continue

                hijri_dates = re.findall(r'date-hijri["\']?>([^<]+)', card)
                greg_dates = re.findall(r'date-gregorian["\']?>([^<]+)', card)

                ev = {
                    'event': title,
                    'hijri_start': hijri_dates[0].strip() if len(hijri_dates) > 0 else '',
                    'hijri_end': hijri_dates[1].strip() if len(hijri_dates) > 1 else '',
                    'gregorian_start': greg_dates[0].strip() if len(greg_dates) > 0 else '',
                    'gregorian_end': greg_dates[1].strip() if len(greg_dates) > 1 else '',
                }
                ev['status'] = _calc_status(ev['gregorian_start'], ev['gregorian_end'], lang)
                events.append(ev)

            key = f"{section_key.replace('bachelor','bachelor').replace('graduate','graduate')}_s{sem_idx+1}"
            data[key] = events

    return data

@router.get("/calendar")
async def get_calendar(year: str = Query("1447", pattern=r"^\d{4}$"), lang: str = Query("ar", pattern=r"^(ar|en)$")):
    return await _fetch_calendar(year, lang)
