"""Command-line tasks for operators.

Run ``python -m app.cli --help``.
(See docs/08-operations.md). In the cloud these run as a Cloud Run job.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.database import get_session_factory


def _db():
    return get_session_factory()()


def cmd_create_admin(args: argparse.Namespace) -> int:
    from app.core.dependencies import get_identity_verifier
    from app.modules.admin_auth import service

    with _db() as db:
        admin = service.create_admin(db, args.email, args.name)
    print(f"Admin access granted to {admin.email}.")
    if get_settings().auth_mode == "firebase" and not args.skip_firebase:
        temporary_password = get_identity_verifier().ensure_admin_account(admin.email, args.name)
        if temporary_password:
            print("A Firebase sign-in account was created with this TEMPORARY password:")
            print(f"  {temporary_password}")
            print("Give it to the admin privately; they should change it after the first sign-in")
            print("(or use 'Forgot password' on the admin login page).")
        else:
            print("The existing Firebase account was found and its email is marked as verified.")
    print("Next: the admin signs in and sets up Google Authenticator (docs/04-firebase-setup.md).")
    return 0


def cmd_deactivate_admin(args: argparse.Namespace) -> int:
    from app.modules.admin_auth import service

    with _db() as db:
        ok = service.deactivate_admin(db, args.email)
    print("Admin access removed." if ok else "No admin with that email.")
    return 0 if ok else 1


def cmd_list_admins(_: argparse.Namespace) -> int:
    from app.modules.admin_auth import service

    with _db() as db:
        for admin in service.list_admins(db):
            state = "active" if admin.is_active else "inactive"
            print(f"{admin.email:40} {state:9} last login: {admin.last_login_at}")
    return 0


def cmd_flush_lead_sync(_: argparse.Namespace) -> int:
    from app.core.dependencies import get_sheets
    from app.modules.lead_sync import service

    with _db() as db:
        result = service.flush(db, get_sheets())
    print(result.model_dump_json())
    return 0


def cmd_generate_exam_template(args: argparse.Namespace) -> int:
    from app.modules.exam.template import build_template

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(build_template())
    print(f"Template written to {target}")
    return 0


def cmd_validate_exam_file(args: argparse.Namespace) -> int:
    from app.modules.exam.service import validate_file

    report = validate_file(Path(args.file).read_bytes())
    print(report.model_dump_json(indent=2))
    return 0 if report.ok else 1


def cmd_check_config(_: argparse.Namespace) -> int:
    settings = get_settings()
    settings.validate_for_environment()
    from app.modules import select_modules

    modules = [m.name for m in select_modules(settings.enabled_modules)]
    print(f"Environment: {settings.app_env}\nModules: {', '.join(modules)}\nConfiguration looks valid.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli", description="College backend operator commands"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-admin", help="Give an email address admin access")
    p.add_argument("--email", required=True)
    p.add_argument("--name")
    p.add_argument(
        "--skip-firebase",
        action="store_true",
        help="Only update the allow-list, not Firebase Auth",
    )
    p.set_defaults(func=cmd_create_admin)

    p = sub.add_parser("deactivate-admin", help="Remove admin access")
    p.add_argument("--email", required=True)
    p.set_defaults(func=cmd_deactivate_admin)

    sub.add_parser("list-admins", help="List admin accounts").set_defaults(func=cmd_list_admins)
    sub.add_parser("flush-lead-sync", help="Retry submissions waiting for Google Sheets").set_defaults(
        func=cmd_flush_lead_sync
    )

    p = sub.add_parser("generate-exam-template", help="Write the Excel template for question sets")
    p.add_argument("--output", default="templates/exam-question-set-template.xlsx")
    p.set_defaults(func=cmd_generate_exam_template)

    p = sub.add_parser("validate-exam-file", help="Check a question-set Excel file without uploading it")
    p.add_argument("file")
    p.set_defaults(func=cmd_validate_exam_file)

    sub.add_parser("check-config", help="Validate the current configuration").set_defaults(
        func=cmd_check_config
    )

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
