"""Import every model so SQLAlchemy and Alembic see the full database schema."""

from app.core.models import Base
from app.modules.admin_auth.models import AdminUser
from app.modules.announcements.models import Announcement
from app.modules.banners.models import Banner
from app.modules.batches.models import Batch
from app.modules.brochures.models import Brochure
from app.modules.courses.models import Course
from app.modules.exam.models import ExamOption, ExamPassage, ExamQuestion, ExamSet
from app.modules.gallery.models import GalleryImage
from app.modules.lead_sync.models import PendingSheetRow
from app.modules.site_settings.models import SiteSettings
from app.modules.videos.models import Video

__all__ = [
    "AdminUser",
    "Announcement",
    "Banner",
    "Base",
    "Batch",
    "Brochure",
    "Course",
    "ExamOption",
    "ExamPassage",
    "ExamQuestion",
    "ExamSet",
    "GalleryImage",
    "PendingSheetRow",
    "SiteSettings",
    "Video",
]
