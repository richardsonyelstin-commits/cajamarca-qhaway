# Cajamarca Qhaway (Fase 1)

Observatorio cívico de monitoreo ciudadano y periodismo de datos anticorrupción para la
región Cajamarca (Perú).

## Alcance Constitucional (Fase 1)

- **Universo (Art. 18)**: 14 entidades públicas verificadas (Gobierno Regional de Cajamarca + 13 Municipalidades Provinciales).
- **Fuentes Oficiales (Art. 10)**: API OCDS del SEACE (`seace-ocds`) y CKAN DataStore del MEF (`mef-datastore`), conservando `raw_payload` íntegro.
- **Revisión Humana Obligatoria (Art. 14)**: Ninguna bandera roja técnica (`RedFlag`) se publica como `Alert` sin revisión nominal acreditada (`005-review-panel`).
- **Explicabilidad Algorítmica (Art. 15)**: Toda alerta publicada expone fórmula, umbral, valor observado, fuente, revisor humano y descargo legal obligatorio.
- **No-Scoring de Personas (Art. 16)** y **Reserva Legal Ley 29733 (Art. 17 / CA-006-01)**.

## Ejecución Local

```bash
pip install -e ".[dev]"
pytest -q
python -m cajamarca_qhaway.cli web audit
python -m cajamarca_qhaway.cli web serve --port 8080
```
