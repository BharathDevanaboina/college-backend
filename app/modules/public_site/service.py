from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.timeutil import utc_now
from app.modules.announcements import service as announcements
from app.modules.banners import service as banners
from app.modules.batches import service as batches
from app.modules.brochures import service as brochures
from app.modules.courses import service as courses
from app.modules.exam import service as exam
from app.modules.gallery import service as gallery
from app.modules.public_site.schemas import (
    PublicAnnouncement,
    PublicBanner,
    PublicBatch,
    PublicCourse,
    PublicGalleryImage,
    PublicSite,
    PublicVideo,
)
from app.modules.site_settings import service as site_settings
from app.modules.videos import service as videos


def build_site(db: Session, settings: Settings) -> PublicSite:
    with_brochure = brochures.course_ids_with_brochure(db)
    active_courses = courses.list_courses(db, active_only=True)
    batches_by_course: dict = {}

    for b in batches.list_public_batches(db):
        batches_by_course.setdefault(b.course_id, []).append(
            PublicBatch(
                id=b.id,
                start_date=b.start_date,
                end_date=b.end_date,
                timings=b.timings,
                mode=b.mode,
            )
        )

    course_items = []
    for c in active_courses:
        out = courses.to_out(c)
        course_items.append(
            PublicCourse(
                **out.model_dump(
                    include={
                        "code",
                        "name",
                        "duration_text",
                        "summary",
                        "eligibility",
                        "total_fee_inr",
                        "total_fee_display",
                        "fee_note",
                        "fee_breakup",
                    }
                ),
                has_brochure=c.id in with_brochure,
                batches=batches_by_course.get(c.id, []),
            )
        )

    banner_items = [
        PublicBanner(
            id=b.id,
            title=b.title,
            image_url=b.image_url,
            thumb_url=b.thumb_url,
            image_width=b.image_width,
            image_height=b.image_height,
            brochure_course_code=(
                b.course.code if b.course and b.course_id in with_brochure else None
            ),
        )
        for b in banners.list_banners(db, active_only=True)
    ]

    return PublicSite(
        settings=site_settings.get_settings_out(db),
        banners=banner_items,
        announcements=[
            PublicAnnouncement(id=a.id, message=a.message, link_url=a.link_url)
            for a in announcements.list_public(db)
        ],
        courses=course_items,
        gallery=[
            PublicGalleryImage(
                id=g.id,
                caption=g.caption,
                image_url=g.image_url,
                thumb_url=g.thumb_url,
                image_width=g.image_width,
                image_height=g.image_height,
            )
            for g in gallery.list_images(db, active_only=True)
        ],
        videos=[
            PublicVideo(
                id=v.id,
                title=v.title,
                platform=v.platform,
                url=v.url,
                embed_url=v.embed_url,
                video_id=v.video_id,
            )
            for v in videos.list_videos(db, active_only=True)
        ],
        exam=exam.exam_info(db, settings),
        generated_at=utc_now(),
    )
