"""The three courses the college offers. Loaded by the first database migration."""

COURSE_CODES = ("IBFAP", "ADV_BCOM", "PGDM")

DEFAULT_COURSES = [
    {
        "code": "IBFAP",
        "name": "IBFAP",
        "duration_text": "45 days",
        "total_fee_inr": 55000,
        "fee_breakup": [],
        "display_order": 1,
    },
    {
        "code": "ADV_BCOM",
        "name": "Advance B.Com",
        "duration_text": "3 years",
        "total_fee_inr": 300000,
        "fee_breakup": [
            {"label": "Year 1", "amount_inr": 100000},
            {"label": "Year 2", "amount_inr": 100000},
            {"label": "Year 3", "amount_inr": 100000},
        ],
        "display_order": 2,
    },
    {
        "code": "PGDM",
        "name": "PGDM",
        "duration_text": "2 years",
        "total_fee_inr": 550000,
        "fee_breakup": [],
        "display_order": 3,
    },
]
