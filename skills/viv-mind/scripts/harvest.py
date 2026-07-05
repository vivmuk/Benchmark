#!/usr/bin/env python3
"""Harvest metadata, summary, and transcript from a URL."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Optional dependencies degrade gracefully if missing.
try:
    import bs4
except ImportError:
    bs4 = None  # type: ignore

try:
    import requests
except ImportError:
    requests = None  # type: ignore


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
URL_RE = re.compile(
    r"(?:https?://|www\.)"  # scheme or www prefix
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}"  # domain
    r"|localhost"  # localhost
    r"|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ip
    r"(?::\d+)?"  # port
    r"(?:[/?]\S*|/?)"  # path/query
    , re.IGNORECASE,
)


@dataclass
class HarvestResult:
    id: str
    timestamp: str
    source_url: str
    source_type: str
    title: str = ""
    author: str = ""
    published_date: str = ""
    summary: str = ""
    key_quotes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    transcript: str = ""
    image_url: str = ""
    language: str = ""
    status: str = "harvested"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _short_uuid() -> str:
    """Return a short url-safe uuid."""
    import uuid
    return uuid.uuid4().hex[:12]


def find_urls(text: str) -> list[str]:
    """Return all HTTP(S) URLs found in text, normalizing www. to https://."""
    urls = URL_RE.findall(text)
    # re.findall returns tuples when groups exist; normalize to strings.
    out: list[str] = []
    for u in urls:
        if isinstance(u, tuple):
            url = "".join(u)
        else:
            url = u
        url = url.strip(',.!?;:\'"')
        if url.startswith("www."):
            url = "https://" + url
        out.append(url)
    return out


def fetch_html(url: str, timeout: int = 20) -> bytes:
    """Fetch raw HTML bytes using urllib."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_html_requests(url: str, timeout: int = 20) -> bytes:
    """Fetch raw HTML bytes using requests if available."""
    if requests is None:
        return fetch_html(url, timeout)
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.content


def _meta_property(soup, prop: str) -> str:
    tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
    return (tag.get("content", "") if tag else "").strip()


def extract_opengraph(html: bytes, base_url: str) -> dict:
    """Extract OpenGraph / Twitter / generic metadata from HTML."""
    if bs4 is None:
        return {}
    soup = bs4.BeautifulSoup(html, "html.parser")
    title = (
        _meta_property(soup, "og:title")
        or _meta_property(soup, "twitter:title")
        or (soup.title.string.strip() if soup.title and soup.title.string else "")
    )
    description = (
        _meta_property(soup, "og:description")
        or _meta_property(soup, "twitter:description")
        or _meta_property(soup, "description")
    )
    image = (
        _meta_property(soup, "og:image")
        or _meta_property(soup, "twitter:image")
        or _meta_property(soup, "twitter:image:src")
    )
    author = (
        _meta_property(soup, "author")
        or _meta_property(soup, "article:author")
    )
    published = (
        _meta_property(soup, "article:published_time")
        or _meta_property(soup, "datePublished")
    )
    site = _meta_property(soup, "og:site_name") or urllib.parse.urlparse(base_url).netloc

    # Make image absolute
    if image and image.startswith("/"):
        parsed = urllib.parse.urlparse(base_url)
        image = f"{parsed.scheme}://{parsed.netloc}{image}"

    return {
        "title": title,
        "summary": description,
        "image_url": image,
        "author": author,
        "published_date": published,
        "site": site,
    }


def extract_body_text(html: bytes, max_chars: int = 3000) -> str:
    """Extract readable body text from HTML."""
    if bs4 is None:
        return ""
    soup = bs4.BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    return text[:max_chars]


def detect_source_type(url: str) -> str:
    """Classify URL or path into article, youtube, tiktok, instagram, video, audio, pdf, generic."""
    netloc = urllib.parse.urlparse(url).netloc.lower()
    path = urllib.parse.urlparse(url).path.lower()
    if "youtube.com" in netloc or "youtu.be" in netloc:
        return "youtube"
    if "tiktok.com" in netloc:
        return "tiktok"
    if "instagram.com" in netloc or "instagr.am" in netloc:
        return "instagram"
    if any(ext in path for ext in (".mp4", ".mov", ".webm", ".mkv")):
        return "video"
    if any(ext in path for ext in (".mp3", ".wav", ".m4a", ".ogg")):
        return "audio"
    if path.endswith(".pdf") or url.lower().endswith(".pdf"):
        return "pdf"
    return "article"


def _run_yt_dlp(url: str, *args: str, timeout: int = 60) -> Optional[str]:
    """Run yt-dlp CLI or python module and return stdout, or None on failure."""
    commands = [
        ["yt-dlp", *args, url],
        [sys.executable, "-m", "yt_dlp", *args, url],
    ]
    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if proc.returncode == 0:
                return proc.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def harvest_video(url: str) -> dict:
    """Harvest video metadata and transcript using yt-dlp."""
    info: dict = {
        "title": "",
        "author": "",
        "published_date": "",
        "summary": "",
        "transcript": "",
        "image_url": "",
        "language": "",
        "duration": "",
    }
    json_output = _run_yt_dlp(
        url,
        "--dump-json",
        "--no-download",
        "--quiet",
        timeout=45,
    )
    if json_output:
        try:
            data = json.loads(json_output)
            info["title"] = data.get("title") or ""
            info["author"] = data.get("uploader") or data.get("channel") or ""
            info["published_date"] = data.get("upload_date") or ""
            info["summary"] = data.get("description") or ""[:500]
            info["image_url"] = (
                data.get("thumbnail")
                or (data.get("thumbnails", [{}])[-1] or {}).get("url")
                or ""
            )
            info["language"] = data.get("language") or ""
            info["duration"] = str(data.get("duration") or "")
        except json.JSONDecodeError:
            pass

    # Try to get transcript via subtitles or auto-generated captions.
    transcript_text = _run_yt_dlp(
        url,
        "--skip-download",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--convert-subs", "srt",
        "--quiet",
        "--no-warnings",
        "-o", "-",
        timeout=90,
    )
    if transcript_text:
        # Strip SRT tags/timestamps roughly.
        lines = []
        for line in transcript_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.isdigit():
                continue
            if " --> " in stripped:
                continue
            if stripped.startswith("<") and stripped.endswith(">"):
                continue
            lines.append(stripped)
        info["transcript"] = " ".join(lines)[:4000]
    return info


def derive_tags(title: str, summary: str, site: str) -> list[str]:
    """Generate simple keyword tags from text."""
    text = f"{title} {summary} {site}".lower()
    candidates = [
        ("ai", "ai"),
        ("art", "art"),
        ("design", "design"),
        ("music", "music"),
        ("politics", "politics"),
        ("science", "science"),
        ("tech", "tech"),
        ("film", "film"),
        ("book", "books"),
        ("health", "health"),
        ("finance", "finance"),
        ("startup", "startup"),
        ("culture", "culture"),
    ]
    tags = [tag for keyword, tag in candidates if keyword in text]
    # Add source domain if available
    if site:
        domain = site.replace("www.", "").split(".")[0]
        if domain and domain not in tags:
            tags.append(domain)
    return tags[:6]


def harvest_pdf(path: str, max_chars: int = 3000) -> dict:
    """Harvest metadata and first-page text from a local PDF."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf required for PDF harvest. Install: pip3 install pypdf")
    reader = PdfReader(path)
    meta = reader.metadata or {}

    # Extract title from first page heading if metadata lacks it
    title = ""
    first_text = ""
    for page in reader.pages:
        try:
            txt = (page.extract_text() or "").strip()
            if txt:
                first_text = txt
                break
        except Exception:
            continue
    lines = [line.strip() for line in first_text.splitlines() if line.strip()]
    # Heuristic: first few short lines often form the title
    if lines:
        title_lines = []
        for line in lines[:6]:
            if len(line) < 120 and not line.lower().startswith(("contents", "executive", "chapter", "by ", "copyright")):
                title_lines.append(line)
            elif title_lines:
                break
        title = " ".join(title_lines).strip()

    # Try metadata title/author
    author = ""
    published_date = ""
    if meta:
        author = (meta.get("/Author") or meta.get("/Creator") or "").strip()
        if isinstance(author, bytes):
            author = author.decode("utf-8", errors="ignore")
        # creation date like D:20260615194613-05'00'
        cd = meta.get("/CreationDate", "")
        if isinstance(cd, bytes):
            cd = cd.decode("utf-8", errors="ignore")
        if cd and cd.startswith("D:"):
            published_date = cd[2:10]

    # Full body text for summary and quotes
    all_text_parts = []
    for page in reader.pages:
        try:
            txt = page.extract_text()
            if txt:
                all_text_parts.append(txt)
        except Exception:
            pass
    full_text = "\n".join(all_text_parts)
    summary_text = full_text.replace(first_text, "").strip() if first_text else full_text.strip()
    summary = summary_text[:max_chars].strip()
    key_quotes = [summary[:240]] if summary else []

    return {
        "title": title or "Untitled",
        "author": author,
        "published_date": published_date,
        "summary": summary,
        "transcript": full_text[:8000],
        "key_quotes": key_quotes,
        "image_url": "",
        "language": "",
    }


def harvest(url: str, fallback_text: str = "") -> HarvestResult:
    """Harvest a single URL or local file path."""
    source_type = detect_source_type(url)
    result = HarvestResult(
        id=_short_uuid(),
        timestamp=_now_iso(),
        source_url=url,
        source_type=source_type,
    )

    if source_type == "pdf":
        pdf_info = harvest_pdf(url)
        result.title = pdf_info.get("title", "")
        result.author = pdf_info.get("author", "")
        result.published_date = pdf_info.get("published_date", "")
        result.summary = pdf_info.get("summary", "")
        result.transcript = pdf_info.get("transcript", "")
        result.image_url = pdf_info.get("image_url", "")
        result.language = pdf_info.get("language", "")
        result.key_quotes = pdf_info.get("key_quotes", [])
        result.tags = derive_tags(result.title, result.summary, "pdf")
    elif source_type in ("youtube", "tiktok", "instagram", "video", "audio"):
        video_info = harvest_video(url)
        result.title = video_info.get("title", "")
        result.author = video_info.get("author", "")
        result.published_date = video_info.get("published_date", "")
        result.summary = video_info.get("summary", "")
        result.transcript = video_info.get("transcript", "")
        result.image_url = video_info.get("image_url", "")
        result.language = video_info.get("language", "")
        if not result.summary and result.transcript:
            result.summary = result.transcript[:500]
    else:
        try:
            html = fetch_html_requests(url)
            og = extract_opengraph(html, url)
            body = extract_body_text(html)
            result.title = og.get("title", "")
            result.author = og.get("author", "")
            result.published_date = og.get("published_date", "")
            result.summary = og.get("summary", "") or body[:500]
            result.image_url = og.get("image_url", "")
            result.key_quotes = [body[:240]] if body else []
            result.tags = derive_tags(result.title, result.summary, og.get("site", ""))
        except Exception as exc:
            result.status = "harvest_failed"
            result.summary = f"Harvest failed: {exc}"

    if not result.title and fallback_text:
        result.title = fallback_text[:120]
    if not result.title:
        result.title = "Untitled"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Harvest metadata from a URL.")
    parser.add_argument("url", help="URL to harvest")
    parser.add_argument("--text", default="", help="Fallback text/title context")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    urls = find_urls(args.url)
    target = urls[0] if urls else args.url.strip()
    result = harvest(target, fallback_text=args.text)

    output = asdict(result)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())