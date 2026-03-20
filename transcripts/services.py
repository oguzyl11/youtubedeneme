import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

import requests
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

SUPADATA_BASE = "https://api.supadata.ai/v1"

_YOUTUBE_ID_RE = re.compile(
    r"(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
)


def extract_youtube_video_id(url: str) -> str | None:
    """Return 11-character YouTube video id if URL matches a known pattern."""
    if not url:
        return None
    url = url.strip()
    m = _YOUTUBE_ID_RE.search(url)
    if m:
        return m.group(1)
    parsed = urlparse(url)
    if "youtube.com" in (parsed.netloc or "").lower():
        if parsed.path.startswith("/watch"):
            q = parse_qs(parsed.query)
            if "v" in q and q["v"]:
                vid = q["v"][0]
                if re.fullmatch(r"[a-zA-Z0-9_-]{11}", vid):
                    return vid
    return None


def fetch_youtube_title(url: str, timeout: float = 10.0) -> str:
    """Best-effort title via YouTube oEmbed (no API key)."""
    oembed = "https://www.youtube.com/oembed"
    try:
        r = requests.get(
            oembed,
            params={"url": url, "format": "json"},
            timeout=timeout,
        )
        if r.status_code == 200:
            data = r.json()
            title = (data.get("title") or "").strip()
            if title:
                return title[:500]
    except (requests.RequestException, ValueError, TypeError):
        pass
    vid = extract_youtube_video_id(url)
    return f"YouTube video ({vid})" if vid else "Video başlığı alınamadı"


def _supadata_headers() -> dict[str, str]:
    api_key = os.environ.get("SUPADATA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "SUPADATA_API_KEY tanımlı değil. `.env` dosyasına ekleyin veya ortam değişkeni ayarlayın."
        )
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _transcript_error_message(error_code: str | None, message: str, details: str) -> str:
    base = (message or "").strip() or "İstek başarısız."
    if details:
        base = f"{base} {details}".strip()
    code_map = {
        "invalid-request": "Geçersiz istek.",
        "transcript-unavailable": "Bu video için transkript yok veya kapalı.",
        "not-found": "Video bulunamadı.",
        "unauthorized": "API anahtarı geçersiz veya eksik.",
        "forbidden": "Bu işlem için yetkiniz yok.",
        "upgrade-required": "Planınız bu işlem için yeterli değil.",
        "limit-exceeded": "Kota veya hız sınırı aşıldı.",
        "internal-error": "Supadata servis hatası.",
    }
    if error_code and error_code in code_map:
        return f"{code_map[error_code]} {base}".strip()
    return base


def _normalize_transcript_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        lines = []
        for chunk in content:
            if not isinstance(chunk, dict):
                continue
            text = (chunk.get("text") or "").strip()
            if not text:
                continue
            offset_ms = chunk.get("offset")
            if isinstance(offset_ms, (int, float)):
                lines.append(f"[{offset_ms / 1000:.1f}s] {text}")
            else:
                lines.append(text)
        return "\n".join(lines).strip()
    return str(content or "").strip()


def _parse_error_response(resp: requests.Response) -> str:
    try:
        data = resp.json()
        if isinstance(data, dict):
            err = data.get("error")
            msg = data.get("message") or ""
            details = data.get("details") or ""
            return _transcript_error_message(
                err if isinstance(err, str) else None,
                msg,
                details if isinstance(details, str) else "",
            )
    except ValueError:
        pass
    return f"API hatası (HTTP {resp.status_code})."


def _poll_job(job_id: str, headers: dict[str, str], timeout_seconds: float = 120.0) -> str:
    url = f"{SUPADATA_BASE}/transcript/{job_id}"
    deadline = time.monotonic() + timeout_seconds
    interval = 2.0
    while time.monotonic() < deadline:
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(_parse_error_response(resp))
        data = resp.json()
        status = data.get("status")
        if status == "completed":
            content = _normalize_transcript_content(data.get("content"))
            if content:
                return content
            raise RuntimeError("Transkript tamamlandı ancak içerik boş.")
        if status == "failed":
            err = data.get("error")
            if isinstance(err, dict):
                msg = _transcript_error_message(
                    err.get("error"),
                    err.get("message") or "",
                    err.get("details") or "",
                )
            else:
                msg = "Transkript işi başarısız oldu."
            raise RuntimeError(msg)
        time.sleep(interval)
    raise RuntimeError("Transkript zaman aşımına uğradı; lütfen tekrar deneyin.")


def fetch_transcript_from_supadata(video_url: str) -> dict[str, Any]:
    """
    Call Supadata transcript API for the given URL (must be a supported platform URL).

    Returns a dict with keys: ok (bool), transcript (str|None), error (str|None), video_id (str|None).
    """
    video_id = extract_youtube_video_id(video_url)
    if video_id is None:
        return {
            "ok": False,
            "transcript": None,
            "error": "YouTube video kimliği çıkarılamadı.",
            "video_id": None,
        }

    try:
        headers = _supadata_headers()
    except RuntimeError as e:
        return {"ok": False, "transcript": None, "error": str(e), "video_id": video_id}

    params = {
        "url": video_url.strip(),
        "text": "true",
        "mode": "auto",
    }
    try:
        resp = requests.get(
            f"{SUPADATA_BASE}/transcript",
            headers=headers,
            params=params,
            timeout=60,
        )
    except requests.RequestException as e:
        return {
            "ok": False,
            "transcript": None,
            "error": f"Ağ hatası: {e}",
            "video_id": video_id,
        }

    if resp.status_code in (200, 202):
        try:
            data = resp.json()
        except ValueError:
            return {
                "ok": False,
                "transcript": None,
                "error": "API geçersiz JSON döndürdü.",
                "video_id": video_id,
            }
        if isinstance(data, dict) and "jobId" in data:
            try:
                text = _poll_job(data["jobId"], headers)
                return {"ok": True, "transcript": text, "error": None, "video_id": video_id}
            except RuntimeError as e:
                return {"ok": False, "transcript": None, "error": str(e), "video_id": video_id}
        if isinstance(data, dict) and "content" in data:
            text = _normalize_transcript_content(data.get("content"))
            if text:
                return {"ok": True, "transcript": text, "error": None, "video_id": video_id}
            return {
                "ok": False,
                "transcript": None,
                "error": "Transkript boş döndü.",
                "video_id": video_id,
            }
        return {
            "ok": False,
            "transcript": None,
            "error": "Beklenmeyen API yanıtı.",
            "video_id": video_id,
        }

    try:
        err = resp.json()
        if isinstance(err, dict) and err.get("error"):
            msg = _transcript_error_message(
                err.get("error"),
                err.get("message") or "",
                err.get("details") or "",
            )
        else:
            msg = _parse_error_response(resp)
    except ValueError:
        msg = f"API hatası (HTTP {resp.status_code})."


    return {"ok": False, "transcript": None, "error": msg, "video_id": video_id}
