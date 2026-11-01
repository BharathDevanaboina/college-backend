from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.modules.courses.schemas import FeeBreakupOut
from app.modules.exam.schemas import ExamInfo
from app.modules.site_settings.schemas import SiteSettingsOut


class PublicBanner(BaseModel):
    id: uuid.UUID
    title: str
    image_url: str
    thumb_url: str
    image_width: int
    image_height: int
    brochure_course_code: str | None  # show the "download brochure" button only when set


class PublicAnnouncement(BaseModel):
    id: uuid.UUID
    message: str
    link_url: str | None


class PublicBatch(BaseModel):
    id: uuid.UUID
    start_date: date
    end_date: date
    timings: str
    mode: str


class PublicCourse(BaseModel):
    code: str
    name: str
    duration_text: str
    summary: str | None
    eligibility: str | None
    total_fee_inr: int
    total_fee_display: str
    fee_note: str | None
    fee_breakup: list[FeeBreakupOut]
    has_brochure: bool
    batches: list[PublicBatch]


class PublicGalleryImage(BaseModel):
    id: uuid.UUID
    caption: str | None
    image_url: str
    thumb_url: str
    image_width: int
    image_height: int


class PublicVideo(BaseModel):
    id: uuid.UUID
    title: str
    platform: str
    url: str
    embed_url: str
    video_id: str


class PublicSite(BaseModel):
    settings: SiteSettingsOut
    banners: list[PublicBanner]
    announcements: list[PublicAnnouncement]
    courses: list[PublicCourse]
    gallery: list[PublicGalleryImage]
    videos: list[PublicVideo]
    exam: ExamInfo
    generated_at: datetime
