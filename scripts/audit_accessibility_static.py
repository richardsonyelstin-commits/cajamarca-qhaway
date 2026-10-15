"""Static WCAG-oriented checks for the project's multipage HTML views."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

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

    tokens = (ROOT / "web/css/tokens.css").read_text(encoding="utf-8")
    def block(selector: str) -> dict[str, str]:
        start = tokens.index(selector) + len(selector)
        body = tokens[start:tokens.index("}", start)]
        return dict(re.findall(r"--([\w-]+):\s*([^;{}]+)", body))

    base = block(":root{")
    for name, overrides in (("dia", {}), ("noche", block('[data-tema="noche"]{'))):
        values = base | overrides
        def color(key: str, palette: dict[str, str] = values) -> str:
            value = palette[key].strip()
            visited = {key}
            while value.startswith("var(--"):
                target = value[6:-1]
                if target in visited:
                    raise ValueError("Token circular")
                visited.add(target)
                value = palette[target].strip()
            return "#" + "".join(character * 2 for character in value[1:]) if len(value) == 4 else value

        pairs = [(foreground, background) for foreground in ("c-texto", "c-texto-2", "c-texto-3", "c-enlace")
                 for background in ("c-fondo", "c-superficie")]
        pairs.append(("c-accion-texto", "c-accion"))
        pairs.extend((f"sev-{severity}-suave-texto", f"sev-{severity}-suave")
                     for severity in ("critica", "alta", "media", "baja"))
        for foreground, background in pairs:
            ratio = relative_contrast(color(foreground), color(background))
            if ratio < 4.5:
                errors.append(f"Contraste {ratio:.2f}:1 para {foreground}/{background} en {name}")
    for page in pages:
        html = page.read_text(encoding="utf-8")
        if 'href="/css/tokens.css"' not in html:
            errors.append(f"{page.name}: no carga los tokens oficiales auditados")

    if errors:
        print("Auditoría estática de accesibilidad: FAIL")
        print("\n".join(errors))
        return 1
    print(f"Auditoría estática de accesibilidad: PASS ({len(pages)} páginas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
