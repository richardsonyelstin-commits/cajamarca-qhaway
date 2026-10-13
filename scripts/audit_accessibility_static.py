"""Static WCAG-oriented checks for the project's multipage HTML views."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.labels: set[str] = set()
        self.controls: list[tuple[dict[str, str], bool]] = []
        self.label_depth = 0
        self.h1_count = 0
        self.title_seen = False
        self.lang_seen = False
        self.aria_references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "html" and data.get("lang"):
            self.lang_seen = True
        if tag == "title":
            self.title_seen = True
        if tag == "label" and data.get("for"):
            self.labels.add(data["for"])
        if tag == "label":
            self.label_depth += 1
        if tag == "h1":
            self.h1_count += 1
        element_id = data.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        if tag in {"input", "select", "textarea"} and data.get("type", "").lower() != "hidden":
            self.controls.append((data, self.label_depth > 0))
        for attribute in ("aria-labelledby", "aria-describedby", "aria-controls"):
            value = data.get(attribute)
            if value:
                self.aria_references.extend((attribute, ref) for ref in value.split())

    def handle_endtag(self, tag: str) -> None:
        if tag == "label" and self.label_depth:
            self.label_depth -= 1


def relative_contrast(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        rgb = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in rgb]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def main() -> int:
    errors: list[str] = []
    pages = sorted((ROOT / "web").glob("*.html"))
    for page in pages:
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        prefix = f"{page.relative_to(ROOT)}: "
        if not parser.lang_seen:
            errors.append(prefix + "falta lang en <html>")
        if not parser.title_seen:
            errors.append(prefix + "falta <title>")
        if parser.h1_count < 1:
            errors.append(prefix + "falta encabezado h1")
        if parser.duplicate_ids:
            errors.append(prefix + f"IDs duplicados: {sorted(parser.duplicate_ids)}")
        for control, nested_label in parser.controls:
            if not (nested_label or control.get("aria-label") or control.get("aria-labelledby") or control.get("id") in parser.labels):
                errors.append(prefix + f"control sin nombre accesible: {control}")
        for attribute, target in parser.aria_references:
            if target not in parser.ids:
                errors.append(prefix + f"{attribute} refiere a ID inexistente: {target}")

    tokens = (ROOT / "web/src/css/tokens.css").read_text(encoding="utf-8")
    light = re.search(r":root,\s*\[data-bs-theme=\"light\"\]\s*\{(?P<body>.*?)\n\}", tokens, flags=re.DOTALL)
    dark = re.search(r"\.dark,\s*\[data-bs-theme=\"dark\"\]\s*\{(?P<body>.*?)\n\}", tokens, flags=re.DOTALL)
    if not light or not dark:
        errors.append("No se pudieron resolver los tokens de color claro y oscuro")
    else:
        for name, background, block in (
            ("tema claro", "#fcf8fa", light.group("body")),
            ("tema oscuro", "#0c111d", dark.group("body")),
        ):
            for token in ("color-civic-emerald", "color-alert-amber"):
                match = re.search(rf"--{token}:\s*(#[0-9a-fA-F]{{6}})", block)
                if not match or relative_contrast(match.group(1), background) < 4.5:
                    errors.append(f"Contraste menor a 4.5:1 para {token} en {name}")

    if errors:
        print("Auditoría estática de accesibilidad: FAIL")
        print("\n".join(errors))
        return 1
    print(f"Auditoría estática de accesibilidad: PASS ({len(pages)} páginas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
