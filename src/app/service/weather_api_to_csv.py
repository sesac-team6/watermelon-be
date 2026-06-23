#!/usr/bin/env python3
"""Fetch daily weather XML from the AgriWeather API and write a cleaned CSV."""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlencode

from app.core.config import settings

BASE_URL = (
    "https://apis.data.go.kr/1390802/AgriWeather/WeatherObsrInfo/V3/"
    "GnrlWeather/getWeatherYearDayList3"
)

COLUMNS: list[tuple[str, str]] = [
    ("tm", "일자"),
    ("avgTa", "기온"),
    ("minTa", "최저기온"),
    ("maxTa", "최고기온"),
    ("sumRn", "강수량"),
    ("avgRhm", "상대습도"),
    ("sumSsHr", "일조시간"),
    ("sumGsr", "일사량"),
    ("avgTs", "평균 지면온도"),
    ("avgCm5Te", "5cm 지중온도"),
    ("avgCm10Te", "10cm 지중온도"),
    ("avgCm20Te", "20cm 지중온도"),
    ("avgCm30Te", "30cm 지중온도"),
]

# The supplied API endpoint uses a regional schema whose tags differ from the
# standard daily-weather names above. Prefer exact names, then these aliases.
SOURCE_ALIASES: dict[str, tuple[str, ...]] = {
    "tm": ("date",),
    "avgTa": ("temp",),
    "minTa": ("lowst_Artmp",),
    "maxTa": ("hghst_Artmp",),
    "sumRn": ("rn",),
    "avgRhm": ("hum",),
    "sumSsHr": ("sun_Time",),
    "sumGsr": ("srqty",),
    "avgTs": ("gr_Temp",),
}


def strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_texts(item: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for child in item:
        values[strip_namespace(child.tag)] = (child.text or "").strip()
    return values


def find_value(row: dict[str, str], field: str) -> tuple[str, str | None]:
    for source_field in (field, *SOURCE_ALIASES.get(field, ())):
        if source_field in row:
            return row[source_field], source_field
    return "", None


def parse_items(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    items = root.findall(".//item")
    return [child_texts(item) for item in items]


def build_weather_url(
    service_key: str,
    search_year: int,
    obsr_spot_cd: str,
    page_no: int = 1,
    page_size: int = 500,
) -> str:
    query = urlencode(
        {
            "serviceKey": service_key,
            "Page_No": page_no,
            "Page_Size": page_size,
            "search_Year": search_year,
            "obsr_Spot_Cd": obsr_spot_cd,
        },
        safe="%",
    )
    return f"{BASE_URL}?{query}"


def fetch_url(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def rows_to_csv(rows: Iterable[dict[str, str]]) -> tuple[str, dict[str, str | None]]:
    used_sources: dict[str, str | None] = {field: None for field, _ in COLUMNS}
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=[label for _, label in COLUMNS])
    writer.writeheader()
    for row in rows:
        cleaned_row = {}
        for field, label in COLUMNS:
            value, source_field = find_value(row, field)
            cleaned_row[label] = value
            used_sources[field] = used_sources[field] or source_field
        writer.writerow(cleaned_row)
    return csv_buffer.getvalue(), used_sources


def weather_xml_to_csv(xml_bytes: bytes) -> tuple[str, dict[str, str | None]]:
    rows = parse_items(xml_bytes)
    if not rows:
        raise ValueError("No <item> rows found in the XML response.")
    return rows_to_csv(rows)


def fetch_weather_csv(
    service_key: str,
    search_year: int,
    obsr_spot_cd: str,
    page_no: int = 1,
    page_size: int = 500,
) -> tuple[str, dict[str, str | None]]:
    url = build_weather_url(
        service_key=service_key,
        search_year=search_year,
        obsr_spot_cd=obsr_spot_cd,
        page_no=page_no,
        page_size=page_size,
    )
    return weather_xml_to_csv(fetch_url(url))


def write_csv(csv_content: str, output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        csv_file.write(csv_content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert AgriWeather daily weather API XML into a cleaned Korean CSV."
        )
    )
    parser.add_argument(
        "--url",
        help="Full API URL to fetch. Overrides service-key/search-year options.",
    )
    parser.add_argument(
        "--service-key",
        default=settings.agri_weather_service_key,
        help="AgriWeather service key. Defaults to AGRI_WEATHER_SERVICE_KEY.",
    )
    parser.add_argument(
        "--search-year",
        type=int,
        default=settings.agri_weather_search_year,
        help="Weather observation year. Defaults to AGRI_WEATHER_SEARCH_YEAR.",
    )
    parser.add_argument(
        "--obsr-spot-cd",
        default=settings.agri_weather_obsr_spot_cd,
        help="Observation spot code. Defaults to AGRI_WEATHER_OBSR_SPOT_CD.",
    )
    parser.add_argument(
        "--page-no",
        type=int,
        default=1,
        help="API page number.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="API page size.",
    )
    parser.add_argument(
        "--input-xml",
        type=Path,
        help="Use a saved XML file instead of calling the API.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="CSV output path.",
    )
    return parser


def default_output_path(search_year: int) -> Path:
    return Path(f"서울시 서초구 {search_year} 일별 기상관측.csv")


def main() -> int:
    args = build_parser().parse_args()

    if args.input_xml:
        xml_bytes = args.input_xml.read_bytes()
    else:
        if args.url:
            url = args.url
        else:
            if not args.service_key:
                print(
                    "Missing service key. Set AGRI_WEATHER_SERVICE_KEY "
                    "or pass --service-key.",
                    file=sys.stderr,
                )
                return 1
            url = build_weather_url(
                service_key=args.service_key,
                search_year=args.search_year,
                obsr_spot_cd=args.obsr_spot_cd,
                page_no=args.page_no,
                page_size=args.page_size,
            )
        xml_bytes = fetch_url(url)

    try:
        csv_content, used_sources = weather_xml_to_csv(xml_bytes)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    output_path = args.output or default_output_path(args.search_year)
    write_csv(csv_content, output_path)
    missing = [field for field, _ in COLUMNS if used_sources[field] is None]

    print(f"Wrote CSV to {output_path}")
    if missing:
        message = "Missing source fields were written as blank columns: "
        print(
            message + ", ".join(missing),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
