"""Dropdown values for the registration form."""

from __future__ import annotations

from app.core.timeutil import ist_now

QUALIFICATIONS = ("CA", "CA Inter", "CMA", "B.Com", "BBA", "MBA", "Other")

CURRENTLY_PURSUING = "Currently Pursuing"
EARLIEST_PASS_YEAR = 1980

INDIAN_STATES_AND_UTS = (
    # States
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    # Union Territories
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
)


def year_options() -> list[str]:
    current = ist_now().year
    return [CURRENTLY_PURSUING] + [
        str(year) for year in range(current, EARLIEST_PASS_YEAR - 1, -1)
    ]
