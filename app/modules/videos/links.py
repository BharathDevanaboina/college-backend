"""Turns a pasted video link into something the website can embed."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
INSTAGRAM_CODE = re.compile(r"^[A-Za-z0-9_-]{5,40}$")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}


@dataclass(frozen=True)
class VideoLink:
    platform: str  # youtube | youtube_short | instagram_reel
    video_id: str
    url: str  # normalised link
    embed_url: str


def youtube(video_id: str, short: bool) -> VideoLink:
    if not YOUTUBE_ID.match(video_id):
        raise ValueError("This does not look like a valid YouTube link.")
    url = (
        f"https://www.youtube.com/shorts/{video_id}"
        if short
        else f"https://www.youtube.com/watch?v={video_id}"
    )
    return VideoLink(
        platform="youtube_short" if short else "youtube",
        video_id=video_id,
        url=url,
        embed_url=f"https://www.youtube-nocookie.com/embed/{video_id}",
    )


def parse_video_link(raw: str) -> VideoLink:
    raw = (raw or "").strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    segments = [s for s in parsed.path.split("/") if s]

    if host == "youtu.be" and segments:
        return youtube(segments[0], short=False)

    if host in YOUTUBE_HOSTS:
        if segments[:1] == ["watch"] or parsed.path == "/watch":
            video_id = (parse_qs(parsed.query).get("v") or [""])[0]
            return youtube(video_id, short=False)
        if len(segments) >= 2 and segments[0] == "shorts":
            return youtube(segments[1], short=True)
        if len(segments) >= 2 and segments[0] in ("embed", "live", "v"):
            return youtube(segments[1], short=False)

    if host in INSTAGRAM_HOSTS and len(segments) >= 2 and segments[0] in ("reel", "reels"):
        code = segments[1]
        if INSTAGRAM_CODE.match(code):
            return VideoLink(
                platform="instagram_reel",
                video_id=code,
                url=f"https://www.instagram.com/reel/{code}/",
                embed_url=f"https://www.instagram.com/reel/{code}/embed",
            )

    raise ValueError("Please paste a YouTube video, YouTube Shorts or Instagram Reel link.")
