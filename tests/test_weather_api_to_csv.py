from datetime import date
from urllib.parse import parse_qs, urlparse

from app.core.config import Settings
from app.service import weather_api_to_csv
from app.service.weather_api_to_csv import (
    build_weather_url,
    default_output_path,
    fetch_weather_csv,
    weather_xml_to_csv,
)


def test_build_weather_url_uses_dynamic_service_key_and_year() -> None:
    url = build_weather_url(
        service_key="test-service-key",
        search_year=2025,
        obsr_spot_cd="137180A001",
        page_no=2,
        page_size=100,
    )

    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    assert parsed_url.scheme == "https"
    assert parsed_url.netloc == "apis.data.go.kr"
    assert query == {
        "serviceKey": ["test-service-key"],
        "Page_No": ["2"],
        "Page_Size": ["100"],
        "search_Year": ["2025"],
        "obsr_Spot_Cd": ["137180A001"],
    }


def test_settings_search_year_defaults_to_current_year() -> None:
    settings = Settings()

    assert settings.agri_weather_search_year == date.today().year


def test_default_output_path_uses_search_year() -> None:
    output_path = default_output_path(search_year=2025)

    assert output_path.name == "서울시 서초구 2025 일별 기상관측.csv"


def test_weather_xml_to_csv_returns_csv_content() -> None:
    xml = b"""
    <response>
        <body>
            <items>
                <item>
                    <date>2026-06-01</date>
                    <temp>21.2</temp>
                    <lowst_Artmp>18.0</lowst_Artmp>
                    <hghst_Artmp>25.4</hghst_Artmp>
                    <rn>1.5</rn>
                    <hum>70.1</hum>
                </item>
            </items>
        </body>
    </response>
    """

    csv_content, used_sources = weather_xml_to_csv(xml)

    assert csv_content.splitlines()[0].startswith("일자,기온,최저기온")
    assert "2026-06-01,21.2,18.0,25.4,1.5,70.1" in csv_content
    assert used_sources["tm"] == "date"
    assert used_sources["avgTa"] == "temp"


def test_fetch_weather_csv_returns_csv_content(monkeypatch) -> None:
    xml = b"""
    <response>
        <body>
            <items>
                <item>
                    <date>2026-06-01</date>
                    <temp>21.2</temp>
                </item>
            </items>
        </body>
    </response>
    """

    def fake_fetch_url(url: str) -> bytes:
        assert "serviceKey=test-service-key" in url
        assert "search_Year=2026" in url
        return xml

    monkeypatch.setattr(weather_api_to_csv, "fetch_url", fake_fetch_url)

    csv_content, used_sources = fetch_weather_csv(
        service_key="test-service-key",
        search_year=2026,
        obsr_spot_cd="137180A001",
    )

    assert "2026-06-01,21.2" in csv_content
    assert used_sources["tm"] == "date"
