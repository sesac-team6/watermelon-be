#!/usr/bin/env python3
"""Fetch KAMIS wholesale price XML and write it as CSV."""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from app.core.config import settings

BASE_URL = "http://www.kamis.or.kr/service/price/xml.do"


def current_month_period(today: date | None = None) -> tuple[date, date]:
    target_date = today or date.today()
    startday = target_date.replace(day=1)
    if startday.month == 12:
        endday = date(startday.year + 1, 1, 1)
    else:
        endday = date(startday.year, startday.month + 1, 1)
    return startday, endday


def strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_texts(item: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for child in item:
        values[strip_namespace(child.tag)] = (child.text or "").strip()
    return values


def parse_items(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    return [child_texts(item) for item in root.findall(".//item")]


def collect_headers(rows: Iterable[dict[str, str]]) -> list[str]:
    headers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                headers.append(key)
                seen.add(key)
    return headers


def build_kamis_url(
    cert_key: str,
    cert_id: str,
    startday: date,
    endday: date,
    product_cls_code: str = "02",
    item_category_code: str = "200",
    item_code: str = "221",
    kind_code: str = "00",
    product_rank_code: str = "04",
    country_code: str = "1101",
    convert_kg_yn: str = "Y",
) -> str:
    query = urlencode(
        {
            "action": "periodProductList",
            "p_productclscode": product_cls_code,
            "p_startday": startday.isoformat(),
            "p_endday": endday.isoformat(),
            "p_itemcategorycode": item_category_code,
            "p_itemcode": item_code,
            "p_kindcode": kind_code,
            "p_productrankcode": product_rank_code,
            "p_countrycode": country_code,
            "p_convert_kg_yn": convert_kg_yn,
            "p_cert_key": cert_key,
            "p_cert_id": cert_id,
            "p_returntype": "xml",
        }
    )
    return f"{BASE_URL}?{query}"


def fetch_url(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def rows_to_csv(rows: list[dict[str, str]]) -> str:
    headers = collect_headers(rows)
    if not headers:
        raise ValueError("No CSV headers found in KAMIS XML items.")

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return csv_buffer.getvalue()


def kamis_xml_to_csv(xml_bytes: bytes) -> str:
    rows = parse_items(xml_bytes)
    if not rows:
        raise ValueError("No <item> rows found in the KAMIS XML response.")
    return rows_to_csv(rows)


def fetch_kamis_csv(
    cert_key: str,
    cert_id: str,
    startday: date,
    endday: date,
    product_cls_code: str = "02",
    item_category_code: str = "200",
    item_code: str = "221",
    kind_code: str = "00",
    product_rank_code: str = "04",
    country_code: str = "1101",
    convert_kg_yn: str = "Y",
) -> str:
    url = build_kamis_url(
        cert_key=cert_key,
        cert_id=cert_id,
        startday=startday,
        endday=endday,
        product_cls_code=product_cls_code,
        item_category_code=item_category_code,
        item_code=item_code,
        kind_code=kind_code,
        product_rank_code=product_rank_code,
        country_code=country_code,
        convert_kg_yn=convert_kg_yn,
    )
    return kamis_xml_to_csv(fetch_url(url))


def write_csv(csv_content: str, output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        csv_file.write(csv_content)


def default_output_path(startday: date, endday: date) -> Path:
    return Path(f"KAMIS 도매가격 {startday.isoformat()}_{endday.isoformat()}.csv")


def build_parser() -> argparse.ArgumentParser:
    default_startday, default_endday = current_month_period()
    parser = argparse.ArgumentParser(
        description="Convert KAMIS wholesale price API XML into CSV."
    )
    parser.add_argument("--url", help="Full API URL to fetch. Overrides options.")
    parser.add_argument(
        "--cert-key",
        default=settings.kamis_cert_key,
        help="KAMIS cert key. Defaults to KAMIS_CERT_KEY.",
    )
    parser.add_argument(
        "--cert-id",
        default=settings.kamis_cert_id,
        help="KAMIS cert id. Defaults to KAMIS_CERT_ID.",
    )
    parser.add_argument(
        "--startday",
        type=date.fromisoformat,
        default=default_startday,
        help="Start date in YYYY-MM-DD format. Defaults to current month first day.",
    )
    parser.add_argument(
        "--endday",
        type=date.fromisoformat,
        default=default_endday,
        help="End date in YYYY-MM-DD format. Defaults to next month first day.",
    )
    parser.add_argument("--product-cls-code", default="02")
    parser.add_argument("--item-category-code", default="200")
    parser.add_argument("--item-code", default="221")
    parser.add_argument("--kind-code", default="00")
    parser.add_argument("--product-rank-code", default="04")
    parser.add_argument("--country-code", default="1101")
    parser.add_argument("--convert-kg-yn", default="Y")
    parser.add_argument(
        "--input-xml",
        type=Path,
        help="Use a saved XML file instead of calling the API.",
    )
    parser.add_argument("--output", type=Path, default=None, help="CSV output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.input_xml:
        xml_bytes = args.input_xml.read_bytes()
    else:
        if args.url:
            url = args.url
        else:
            if not args.cert_key or not args.cert_id:
                print(
                    "Missing KAMIS credentials. Set KAMIS_CERT_KEY/KAMIS_CERT_ID "
                    "or pass --cert-key/--cert-id.",
                    file=sys.stderr,
                )
                return 1
            url = build_kamis_url(
                cert_key=args.cert_key,
                cert_id=args.cert_id,
                startday=args.startday,
                endday=args.endday,
                product_cls_code=args.product_cls_code,
                item_category_code=args.item_category_code,
                item_code=args.item_code,
                kind_code=args.kind_code,
                product_rank_code=args.product_rank_code,
                country_code=args.country_code,
                convert_kg_yn=args.convert_kg_yn,
            )
        xml_bytes = fetch_url(url)

    try:
        csv_content = kamis_xml_to_csv(xml_bytes)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    output_path = args.output or default_output_path(args.startday, args.endday)
    write_csv(csv_content, output_path)
    print(f"Wrote CSV to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
