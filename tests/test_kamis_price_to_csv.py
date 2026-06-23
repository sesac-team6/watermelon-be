from datetime import date
from urllib.parse import parse_qs, urlparse

from app.service import kamis_price_to_csv
from app.service.kamis_price_to_csv import (
    build_kamis_url,
    current_month_period,
    fetch_kamis_csv,
    kamis_xml_to_csv,
)


def test_current_month_period_uses_first_days() -> None:
    startday, endday = current_month_period(today=date(2026, 6, 22))

    assert startday == date(2026, 6, 1)
    assert endday == date(2026, 7, 1)


def test_build_kamis_url_uses_dynamic_credentials_and_dates() -> None:
    url = build_kamis_url(
        cert_key="test-cert-key",
        cert_id="test-cert-id",
        startday=date(2026, 6, 1),
        endday=date(2026, 7, 1),
    )

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    assert parsed_url.netloc == "www.kamis.or.kr"
    assert query["p_startday"] == ["2026-06-01"]
    assert query["p_endday"] == ["2026-07-01"]
    assert query["p_cert_key"] == ["test-cert-key"]
    assert query["p_cert_id"] == ["test-cert-id"]


def test_kamis_xml_to_csv_returns_csv_content() -> None:
    xml = b"""
    <document>
        <data>
            <item>
                <regday>2026-06-01</regday>
                <price>10000</price>
            </item>
            <item>
                <regday>2026-06-02</regday>
                <price>11000</price>
            </item>
        </data>
    </document>
    """

    csv_content = kamis_xml_to_csv(xml)

    assert csv_content.splitlines() == [
        "regday,price",
        "2026-06-01,10000",
        "2026-06-02,11000",
    ]


def test_fetch_kamis_csv_returns_csv_content(monkeypatch) -> None:
    xml = b"""
    <document>
        <data>
            <item>
                <regday>2026-06-01</regday>
                <price>10000</price>
            </item>
        </data>
    </document>
    """

    def fake_fetch_url(url: str) -> bytes:
        assert "p_cert_key=test-cert-key" in url
        assert "p_cert_id=test-cert-id" in url
        return xml

    monkeypatch.setattr(kamis_price_to_csv, "fetch_url", fake_fetch_url)

    csv_content = fetch_kamis_csv(
        cert_key="test-cert-key",
        cert_id="test-cert-id",
        startday=date(2026, 6, 1),
        endday=date(2026, 7, 1),
    )

    assert csv_content.splitlines() == [
        "regday,price",
        "2026-06-01,10000",
    ]
