"""Display helpers."""

from __future__ import annotations


def format_inr(amount: int) -> str:
    """Indian digit grouping: 550000 -> '₹5,50,000'."""
    sign = "-" if amount < 0 else ""
    digits = str(abs(int(amount)))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups) + "," + tail
    return f"{sign}₹{digits}"
