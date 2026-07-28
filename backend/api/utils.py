from datetime import date


def current_year_week() -> tuple[int, int]:
    iso = date.today().isocalendar()
    return iso.year, iso.week


def row_to_dict(row):
    return dict(row)