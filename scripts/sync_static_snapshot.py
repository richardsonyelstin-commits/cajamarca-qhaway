"""Sincroniza cifras iniciales de vistas MPA desde verified-snapshot.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "web" / "src" / "data" / "verified-snapshot.json"


def _replace_element(html: str, element_id: str, value: str) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[a-zA-Z][\w:-]*)\b(?=[^>]*\bid="{re.escape(element_id)}")[^>]*>).*?(</(?P=tag)\s*>)',
        re.DOTALL,
    )
    updated, count = pattern.subn(lambda match: match.group(1) + value + match.group(3), html, count=1)
    if count == 0:
        raise ValueError(f"No se encontro el elemento HTML #{element_id}")
    return updated


def _replace_style_width(html: str, element_id: str, width: str) -> str:
    pattern = re.compile(rf'(<[^>]*\bid="{re.escape(element_id)}"[^>]*\bstyle=")([^"]*)(")')
    updated, count = pattern.subn(lambda match: match.group(1) + f"width: {width}" + match.group(3), html, count=1)
    if count == 0:
        raise ValueError(f"No se encontro style para #{element_id}")
    return updated


def _replace_attribute_values(html: str, attribute: str, value: str) -> str:
    pattern = re.compile(rf'(<[^>]*\b{re.escape(attribute)}\b[^>]*>).*?(</[^>]+\s*>)', re.DOTALL)
    return pattern.sub(lambda match: match.group(1) + value + match.group(2), html)


def sync_static_snapshot() -> list[Path]:
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    metadata = data["metadata"]
    procurements = int(metadata["total_procurements"])
    published_alerts = int(metadata["total_published_alerts"])
    entities = int(metadata["total_entities"])
    works = int(metadata["total_geospatial_works"])
    budgets = data.get("budget_execution_records", [])
    current_year = max((int(row["fiscal_year"]) for row in budgets), default=0)
    current_budget = [row for row in budgets if int(row["fiscal_year"]) == current_year]
    current_entities = len({row["entity_id"] for row in current_budget})
    pim_total = sum(float(row["budgeted_amount"]) for row in current_budget)
    devengado_total = sum(float(row["executed_amount"]) for row in current_budget)
    execution_pct = (devengado_total / pim_total * 100) if pim_total else None
    pim_text = f"S/ {pim_total:,.0f}" if current_entities == entities else "Cobertura MEF parcial"
    devengado_text = f"S/ {devengado_total:,.0f}" if current_entities == entities else "Cobertura MEF parcial"
    execution_text = f"{execution_pct:.1f}%" if current_entities == entities and execution_pct is not None else "No calculable"
    replacements: dict[str, dict[str, str]] = {
        "index.html": {
            "hero-total-pim": pim_text,
            "kpi-pim-total": pim_text,
            "kpi-devengado-pct": execution_text,
            "kpi-devengado-pocket": f"Corte fiscal {current_year}: {current_entities}/{entities} entidades",
            "kpi-devengado-narrative": f"Devengado {devengado_text} sobre PIM {pim_text} al corte MEF disponible.",
            "speedo-text-pct": execution_text,
            "kpi-procurements-total": f"{procurements} procesos SEACE",
            "kpi-procurements-sub": f"{procurements} registros oficiales sincronizados.",
            "kpi-alerts-total": f"{published_alerts} alertas publicadas",
            "index-total-procurements-badge": str(procurements),
        },
        "alertas.html": {
            "alertas-kpi-total": str(published_alerts),
            "alertas-kpi-severity-sub": "No hay alertas publicadas",
            "alertas-kpi-monto": "Sin monto publicado",
            "alertas-kpi-monto-sub": "No hay expedientes con dictamen publicado",
            "alertas-kpi-entidades": f"0 / {entities}",
            "alertas-kpi-entidades-sub": "Entidades con alertas publicadas",
            "alertas-kpi-explicabilidad": "No aplica",
        },
        "entidades.html": {
            "entidades-kpi-pim": pim_text,
            "entidades-kpi-devengado": devengado_text,
            "entidades-kpi-ejecucion": execution_text,
            "entidades-kpi-contratos": str(procurements),
            "entidades-kpi-alertas-sub": f"{published_alerts} alertas publicadas",
        },
        "presupuesto.html": {
            "kpi-pim": pim_text,
            "kpi-dev": devengado_text,
            "kpi-exec-rate": execution_text,
            "kpi-critical-count": str(sum(1 for row in current_budget if float(row["budgeted_amount"]) > 0 and float(row["executed_amount"]) / float(row["budgeted_amount"]) < 0.3)) if current_entities == entities else "No evaluable",
            "kpi-critical-sub": f"Pliegos con devengado <30% del PIM ({current_year})" if current_entities == entities else "Cobertura MEF parcial",
        },
        "georreferenciacion.html": {
            "kpi-total-works": f"{works} obras verificadas",
            "kpi-critical-count": "0 casos",
            "kpi-sar-rescued": "Sin escenas verificadas",
        },
        "entidad-detalle.html": {
            "dossier-flags-count": f"{published_alerts} alertas publicadas",
            "kpi-pim": "Sin dato MEF",
            "kpi-devengado": "Sin dato MEF",
            "kpi-pct": "No calculable",
            "kpi-procurements-count": "Se carga desde SEACE",
            "kpi-canon-count": "Sin dato MEF",
        },
        "contrato-detalle.html": {
            "kpi-awarded-amount": "Sin dato SEACE",
            "kpi-bidders": "Sin dato SEACE",
            "kpi-bidders-label": "Se carga desde el registro verificado",
            "kpi-supplier-ruc": "Sin dato SEACE",
        },
    }
    style_updates = {
        "index.html": {"kpi-devengado-bar": execution_text},
        "entidades.html": {"entidades-kpi-bar": execution_text},
    }

    updated_paths: list[Path] = []
    for filename, values in replacements.items():
        path = ROOT / "web" / filename
        html = path.read_text(encoding="utf-8")
        for element_id, value in values.items():
            html = _replace_element(html, element_id, value)
        for element_id, width in style_updates.get(filename, {}).items():
            html = _replace_style_width(html, element_id, width)
        if filename == "index.html":
            html = html.replace(
                "3 alertas validadas formalmente por revisores humanos (Art. 14).",
                f"{published_alerts} alertas publicadas; sin actas humanas verificadas en este corte.",
            )
            html = html.replace("14 Pliegos sincronizados", f"{entities} entidades en universo canónico")
            html = html.replace("12 Reglas algorítmicas públicas", "10 indicadores configurados")
            html = html.replace(
                "Accede a los datasets consolidados de contrataciones SEACE y presupuesto MEF para las 14 entidades fiscalizadas en formatos interoperables (.CSV, .JSON OCDS Releases, .PARQUET).",
                f"Consulta {procurements} contrataciones oficiales SEACE verificadas. La cobertura presupuestal MEF es parcial; revisa los años y entidades disponibles antes de comparar montos.",
            )
            html = _replace_attribute_values(html, "data-radar-pim", pim_text)
            html = _replace_attribute_values(html, "data-radar-rate", execution_text)
            html = re.sub(
                r'(<div[^>]*\bdata-radar-bar\b[^>]*\bstyle=")[^"]*(")',
                lambda match: match.group(1) + f"width: {execution_text}" + match.group(2),
                html,
            )
            for stale in (
                "S/ 7,337.4 Millones",
                "S/ 7,337.4 M",
                "aprox. S/ 4,890 por habitante",
                "aprox. S/ 4,890 por cada cajamarquino",
                "S/ 1,974.4 M",
                "S/ 73 de cada S/ 100",
                "Meta Semestral: 45.0% · Brecha: +28.1 p.p. (Superando la meta)",
                "Meta semestral superada en transferencias e inversiones",
                "Canon minero en ejecución; alertas en contrataciones directas",
                "3 Alertas Publicadas · 0 alertas publicadas detectadas.",
            ):
                html = html.replace(stale, "Dato no disponible por cobertura MEF parcial")
            html = re.sub(r"\d+ Banderas Rojas?", "0 alertas publicadas", html)
            html = re.sub(r"\d+ Banderas", "0 alertas publicadas", html)
            for stale_cui in ("CUI 2348910", "CUI 2195041"):
                html = html.replace(stale_cui, "CUI sin verificacion")
            for stale_pct in ("90.0%", "24.0%", "65.0%", "62.0%"):
                html = html.replace(stale_pct, "No disponible")
            for stale_amount in ("S/ 5,351.2 M", "S/ 228.1 M", "S/ 94.5 M", "S/ 93.9 M", "S/ 429.3 M"):
                html = html.replace(stale_amount, "Sin dato MEF")
            html = re.sub(r"RUC \d{11} · Pliego \d+", "Entidad del universo canónico", html)
            html = re.sub(
                r'(<p class="text-body-sm text-on-surface-variant leading-relaxed">\s*)Contrato registrado con devengado financiero del .*?(</p>)',
                r'\1No hay un CUI con coordenadas verificadas, registros presupuestales completos y escenas satelitales validadas para calcular una divergencia.\2',
                html,
                count=1,
                flags=re.DOTALL,
            )
            html = re.sub(
                r'(<p class="text-body-sm text-on-surface-variant leading-relaxed">\s*)Supervisión física continua de obras hospitalarias\..*?(</p>)',
                r'\1No hay un CUI con coordenadas verificadas, registros presupuestales completos y escenas satelitales validadas para comparar avances.\2',
                html,
                count=1,
                flags=re.DOTALL,
            )
            html = html.replace("Caso Real 1: Divergencia Critica Observable", "Cobertura satelital disponible")
            html = html.replace("Divergencia Crítica GEO-001", "Sin señales geoespaciales verificadas")
            html = html.replace("Pavimentación y Drenaje Pluvial Integral Av. Héroes del Cenepa", "Sin obra con CUI validado")
            html = html.replace("Contrato registrado con devengado financiero del 90.0% en MEF SIAF, mientras que el análisis multi-temporal con radar SAR Sentinel-1 y óptico Sentinel-2 registra solo 24.0% de actividad estructural efectiva.", "No hay un CUI con coordenadas verificadas, registros presupuestales completos y escenas satelitales validadas para calcular una divergencia.")
            html = html.replace("Respaldo SAR Anti-Nubosidad Activo", "Escenas verificadas: 0")
            html = html.replace("Caso Real 2: Monitoreo Regional Conforme", "Cobertura satelital disponible")
            html = html.replace("Conforme / En Proceso", "Sin comparación verificada")
            html = html.replace("Mejoramiento de Servicios del Hospital Regional Docente", "Sin obra con CUI validado")
            html = html.replace("Supervisión física continua de obras hospitalarias. La firma espectral y backscatter de radar confirman movimiento de estructuras y concordancia con cronograma financiero.", "No hay un CUI con coordenadas verificadas, registros presupuestales completos y escenas satelitales validadas para comparar avances.")
            html = html.replace("Concordancia F-F Evaluada", "Sin comparación verificada")
        elif filename == "entidad-detalle.html":
            siaf_corrections = {
                "300600": "300549", "300601": "300562", "300602": "300566",
                "300603": "300578", "300604": "300597", "300606": "300620",
                "300607": "300623", "300608": "300635", "300609": "300642",
                "300610": "300649", "300611": "300662", "300612": "300666",
            }
            html = re.sub(
                r"(siaf:\s*')([0-9]+)(')",
                lambda match: match.group(1) + siaf_corrections.get(match.group(2), match.group(2)) + match.group(3),
                html,
            )
            html = re.sub(r"titular:\s*'[^']*'", "titular: 'Sin dato verificado'", html)
            html = re.sub(r"sede:\s*'[^']*'", "sede: 'Sede institucional no verificada'", html)
            html = re.sub(r'width:\s*\d+(?:\.\d+)?%', 'width: 0%', html)
            for stale_amount in (
                "S/ 1,120,540,200", "S/ 303,666,800", "S/ 1,290,304,990",
                "S/ 279,757,935", "S/ 1,263,282,880", "S/ 798,012,400", "S/ 197,689,300",
            ):
                html = html.replace(stale_amount, "Sin dato MEF")
            for stale_pct in ("72.9%", "27.1%", "19.8%", "52.4%", "33.1%", "8.2%", "75.3%"):
                html = html.replace(stale_pct, "No disponible")
            html = html.replace("Brecha: +30.3 p.p.", "Brecha: no calculable")
            html = html.replace("Rubros SIAF 18, 00, 09 y 19", "Rubros MEF: cobertura parcial")
            html = html.replace("Se evidencia un sesgo operativo: los recursos destinados a gasto corriente (operación y planillas) presentan mayor tracción porcentual respecto al rubro de capital y obras de impacto social directo.", "La cobertura MEF disponible no permite comparar categorías de gasto para esta entidad.")
        elif filename in {"entidades.html", "presupuesto.html"}:
            html = html.replace("S/ 73 de cada S/ 100", "No calculable con cobertura parcial")
            html = html.replace("Meta superada (Meta semestral: 45%)", "Cobertura MEF parcial; avance no calculable")
            if filename == "entidades.html":
                html = re.sub(r">(?:52\.4|32\.6|15\.0)%<", ">No disponible<", html)
                html = re.sub(r'width:\s*\d+(?:\.\d+)?%', 'width: 0%', html)
        path.write_text(html, encoding="utf-8", newline="")
        updated_paths.append(path)
    return updated_paths


if __name__ == "__main__":
    for path in sync_static_snapshot():
        print(path.relative_to(ROOT).as_posix())
