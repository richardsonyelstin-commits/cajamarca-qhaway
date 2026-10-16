from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path


class Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.data: set[tuple[str, str]] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        self.data.update((key, value or "") for key, value in attrs if key.startswith("data-"))


def test_dom_anchor_baseline_is_preserved() -> None:
    baseline = json.loads(Path("context/snapshots/2026-10-15-dom-anchor-baseline.json").read_text(encoding="utf-8"))
    for filename, expected in baseline["html"].items():
        parser = Anchors()
        parser.feed((Path("web") / filename).read_text(encoding="utf-8"))
        assert set(expected["ids"]) <= set(parser.ids), filename
        assert len(parser.ids) == len(set(parser.ids)), filename
        prose = {"data-ciudadano", "data-especialista", "data-citizen", "data-expert"}
        assert {tuple(item) for item in expected["data_attributes"] if item[0] not in prose} <= parser.data, filename
        assert {key for key, _ in expected["data_attributes"]} <= {key for key, _ in parser.data}, filename


def test_login_and_dom_baseline_contain_no_embedded_credentials() -> None:
    parser = Anchors()
    parser.feed(Path("web/login.html").read_text(encoding="utf-8"))
    baseline = json.loads(
        Path("context/snapshots/2026-10-15-dom-anchor-baseline.json").read_text(encoding="utf-8")
    )
    banned = {"data-pass", "data-email"}
    assert not any(key in banned for key, _ in parser.data)
    assert not any(key in banned for key, _ in baseline["html"]["login.html"]["data_attributes"])


def test_official_brand_assets_are_self_hosted() -> None:
    for source in Path("identidad-qhaway/web").rglob("*"):
        if source.is_file():
            target = Path("web") / source.relative_to("identidad-qhaway/web")
            assert target.is_file(), target
            assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest(), target
    for page in Path("web").glob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in html, page
        assert "cdn.tailwindcss.com" not in html, page
        assert '/css/tokens.css' in html and '/css/fonts.css' in html and '/css/brand.css' in html, page
        assert '/media/logo/logo-horizontal-negativo.svg' in html, page
