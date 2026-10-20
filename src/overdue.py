from datetime import date


def with_overdue(row) -> dict:
    """Return the row as a dict with is_overdue set. A missing or past date is overdue."""
    asset = dict(row)
    due = asset["next_service_date"]
    asset["is_overdue"] = due is None or due < date.today().isoformat()
    return asset
