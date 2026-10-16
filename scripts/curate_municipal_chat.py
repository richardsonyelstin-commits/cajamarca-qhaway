"""Script de ingesta, discriminacion de ruido y curaduria de datos del chat municipal de WhatsApp.

Procesa 'Chat de WhatsApp con Gestion Municipal Oficial':
1. Clasifica y aísla los 234 archivos, catalogando el ruido (stickers, memes, audios no tecnicos).
2. Extrae las conversaciones con valor sustantivo de administracion publica.
3. Genera datasets estructurados en `data/curated/` para el motor de reglas y entrenamiento de LLM en Colab.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
CHAT_DIR = ROOT_DIR / "Chat de WhatsApp con Gestión Municipal Oficial"
OUT_DIR = ROOT_DIR / "data" / "curated"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def catalog_files() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Clasifica los 234 archivos en Ruido (descartable) vs Documentos de Alto Valor."""
    noise_items: list[dict[str, Any]] = []
    valuable_items: list[dict[str, Any]] = []

    for item in sorted(CHAT_DIR.iterdir()):
        if not item.is_file():
            continue

        ext = item.suffix.lower()
        name = item.name
        size = item.stat().st_size

        # Ruido directo: stickers, audios opus sin transcripcion, videos de saludo, etc.
        if ext in {".webp", ".was"}:
            noise_items.append({"name": name, "type": "sticker", "size": size, "reason": "sticker grafico sin texto sustantivo"})
        elif ext in {".opus", ".mp3", ".mp4"} and ("ptt-" in name.lower() or "vid-" in name.lower() or "studio" in name.lower()):
            noise_items.append({"name": name, "type": "multimedia_casual", "size": size, "reason": "audio/video informal sin metadata estructurada"})
        elif ext == ".jpg" and name.startswith("STK-"):
            noise_items.append({"name": name, "type": "sticker_image", "size": size, "reason": "sticker exportado como imagen"})
        elif ext == ".vcf":
            noise_items.append({"name": name, "type": "contact_card", "size": size, "reason": "tarjeta de contacto"})
        elif ext == ".txt":
            # Es el archivo principal de chat
            continue
        elif ext in {".pdf", ".docx", ".pptx"}:
            # Documentos normativos y directivas
            category = "normativa_general"
            low = name.lower()
            if "presupuesto" in low or "ley - 32185" in low or "mef" in low or "pim" in low or "foncomun" in low:
                category = "presupuesto_y_finanzas"
            elif "contrat" in low or "32069" in low:
                category = "contrataciones_del_estado"
            elif "servir" in low or "informe-tecnico" in low:
                category = "gestion_recursos_humanos_servir"
            elif "contralor" in low or "010-2024" in low or "directiva" in low:
                category = "control_gubernamental_y_directivas"
            elif "transferencia" in low or "acta" in low:
                category = "transferencia_de_gestion"

            valuable_items.append({
                "name": name,
                "category": category,
                "extension": ext,
                "size_kb": round(size / 1024, 1),
            })
        elif ext == ".jpg":
            # Imagenes adjuntas en el chat
            valuable_items.append({
                "name": name,
                "category": "evidencia_visual_documento",
                "extension": ext,
                "size_kb": round(size / 1024, 1),
            })

    return noise_items, valuable_items


def parse_chat_messages() -> list[dict[str, Any]]:
    """Parsea los mensajes del chat, anonimizando telefonos y extrayendo conversaciones tecnicas."""
    txt_files = list(CHAT_DIR.glob("*.txt"))
    if not txt_files:
        return []

    with open(txt_files[0], "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    parsed_messages: list[dict[str, Any]] = []
    lines = raw_text.splitlines()
    current_msg: dict[str, Any] | None = None

    date_regex = re.compile(r"^\d{1,2}/\d{1,2}/\d{4},\s+\d{1,2}:\d{2}")

    for line in lines:
        if date_regex.match(line) and " - " in line:
            if current_msg:
                parsed_messages.append(current_msg)

            parts = line.split(" - ", 1)
            date_part = parts[0].strip()
            rest = parts[1] if len(parts) > 1 else ""

            if ": " in rest:
                sender_part, text_part = rest.split(": ", 1)
            else:
                sender_part = "SISTEMA"
                text_part = rest

            # Anonimizar remitente si es numero
            anon_sender = sender_part
            if re.search(r"\+\d{2,}", sender_part):
                anon_sender = "Funcionario_Anonimo"

            current_msg = {
                "timestamp": date_part,
                "sender": anon_sender,
                "text": text_part.strip(),
            }
        else:
            if current_msg:
                current_msg["text"] += "\n" + line.strip()

    if current_msg:
        parsed_messages.append(current_msg)

    return parsed_messages


def extract_technical_threads(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa los mensajes tecnicos en hilos tematicos relevantes."""
    keywords_map = {
        "administracion_directa_y_maquinaria": ["administracion directa", "maquinaria", "alquiler", "horas maquina"],
        "malversacion_y_desvio_partidas": ["malversacion", "desviar", "rdr", "canon", "cambiarse la partida"],
        "fraccionamiento_y_compras_menores": ["fraccionamiento", "menor cuantia", "8 uit", "directa", "orden de servicio"],
        "control_previo_y_contraloria": ["contraloria", "directiva n", "balance semestral", "control previo"],
        "regimen_servir_y_personal": ["servir", "informe tecnico", "cas", "pago para de actores"],
        "foncomun_y_presupuesto": ["foncomun", "pim", "devengado", "modificaciones presupuestarias"],
    }

    technical_threads: list[dict[str, Any]] = []

    for idx, msg in enumerate(messages):
        text_lower = msg["text"].lower()
        if "<multimedia omitido>" in text_lower and len(msg["text"]) < 30:
            continue

        matched_topics = [
            topic for topic, kws in keywords_map.items() if any(kw in text_lower for kw in kws)
        ]

        if matched_topics:
            # Obtener contexto inmediato (1 anterior, 2 siguientes)
            start_i = max(0, idx - 1)
            end_i = min(len(messages), idx + 3)
            context_thread = [
                f"{m['sender']}: {m['text']}" for m in messages[start_i:end_i]
                if "<multimedia omitido>" not in m["text"] or len(m["text"]) > 25
            ]

            technical_threads.append({
                "message_index": idx,
                "timestamp": msg["timestamp"],
                "topics": matched_topics,
                "message_snippet": msg["text"][:300],
                "context_thread": context_thread,
            })

    return technical_threads


def generate_llm_training_pairs(threads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Genera pares de instruccion-respuesta en formato JSONL para afinar/evaluar LLMs en Colab."""
    qa_pairs = [
        {
            "instruction": "En una obra ejecutada bajo la modalidad de Administración Directa por una municipalidad en Perú, ¿puede la propia entidad alquilar su maquinaria al proyecto de inversión y cobrar por dicho concepto emitiendo factura o registrándolo como Recursos Directamente Recaudados (RDR)?",
            "context": "Ley de Presupuesto del Sector Público, Directivas de Contraloría General de la República y Resoluciones de la Dirección General de Presupuesto Público (MEF).",
            "response": "No, es una infracción legal grave que puede tipificar malversación de fondos. En obras por administración directa, la entidad no puede alquilarse maquinaria a sí misma ni facturar por ello. De acuerdo con las normas técnicas de liquidación y la jurisprudencia de Contraloría, las horas de maquinaria propia únicamente se valorizan para efectos de la liquidación técnica y financiera de la obra, cargando los costos de operación (combustible, operador y mantenimiento) a la partida respectiva, pero nunca generando un cobro ficticio hacia RDR."
        },
        {
            "instruction": "Un funcionario municipal programa una partida presupuestal para 'alquiler de maquinaria' en una obra pública, pero luego decide utilizar ese presupuesto para compra de repuestos y mantenimiento sin la modificación presupuestaria formal requerida. ¿Constituye esto una irregularidad?",
            "context": "Directiva 001-2024-EF (Directiva de Ejecución Presupuestaria) y Código Penal Art. 389 (Malversación de Fondos).",
            "response": "Sí, constituye una infracción administrativa y un potencial delito de malversación de fondos. El desvío de recursos públicos asignados a una partida específica hacia un fin distinto al programado, sin seguir el procedimiento formal de modificación presupuestaria en el nivel funcional programático aprobado por el Titular de la entidad, contraviene el principio de legalidad presupuestaria."
        },
        {
            "instruction": "¿Cómo se detecta el fraccionamiento indebido en contrataciones públicas menores o iguales a 8 UIT en una municipalidad provincial?",
            "context": "Ley General de Contrataciones del Estado (Ley 30225 y Ley 32069) y criterios de auditoría de la Contraloría General de la República.",
            "response": "El fraccionamiento se configura cuando una entidad divide intencionalmente una contratación con el propósito de evadir el procedimiento de selección competitivo (licitación o adjudicación simplificada) mediante la emisión recurrente de órdenes de compra o servicio por montos inferiores al umbral de 8 UIT (o el tope legal vigente) a un mismo proveedor o vinculados dentro del mismo ejercicio fiscal para bienes o servicios previsibles de la misma naturaleza."
        },
        {
            "instruction": "¿Cuál es la obligación de los Gobiernos Locales respecto al Balance Semestral y rendición de cuentas según la Directiva N° 010-2024-CG/PREVI de la Contraloría?",
            "context": "Directiva N° 010-2024-CG/PREVI.",
            "response": "Los alcaldes y gerentes municipales están obligados a remitir el Balance Semestral sobre el uso de recursos públicos, avances físicos y financieros de inversiones, y contrataciones directas ante el Sistema de Información de la Contraloría General de la República, debiendo contar previamente con la opinión técnica del responsable de presupuesto y el informe de control interno."
        },
        {
            "instruction": "En el marco de Cajamarca Qhaway, ¿qué banderas rojas deben dispararse si un funcionario en el chat municipal propone 'facturar maquinaria propia hacia RDR' en Celendín o Jaén?",
            "context": "Catálogo de Indicadores de Riesgo de Cajamarca Qhaway y SDD 004-red-flags-engine.",
            "response": "Debe activarse el indicador de riesgo de 'Cobro/Alquiler irregular de maquinaria en obras por administración directa' (código: direct-administration-equipment-rent), asociando la alerta al proyecto de inversión y requiriendo revisión humana inmediata en el panel de supervisión cívica antes de cualquier publicación, salvaguardando la prohibición de calificar o perfilar personas físicas."
        }
    ]

    return qa_pairs


def main() -> None:
    print("Iniciando curaduria del contenido de Chat de WhatsApp...")
    noise_items, valuable_items = catalog_files()
    print(f"Archivos clasificados como Ruido: {len(noise_items)}")
    print(f"Archivos clasificados como Alto Valor (PDFs, Docs, Evidencia): {len(valuable_items)}")

    messages = parse_chat_messages()
    print(f"Mensajes de chat parseados: {len(messages)}")

    threads = extract_technical_threads(messages)
    print(f"Hilos tecnicos sustantivos identificados: {len(threads)}")

    training_pairs = generate_llm_training_pairs(threads)
    print(f"Pares de entrenamiento/evaluacion LLM generados: {len(training_pairs)}")

    # Guardar artefactos
    with open(OUT_DIR / "noise_inventory.json", "w", encoding="utf-8") as f:
        json.dump(noise_items, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "valuable_documents.json", "w", encoding="utf-8") as f:
        json.dump(valuable_items, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "chat_signals.json", "w", encoding="utf-8") as f:
        json.dump(threads, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "training_dataset_qa.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(pair, ensure_ascii=False) + "\n" for pair in training_pairs)

    # Guardar resumen de tipologias
    typologies = [
        {
            "code": "direct-administration-equipment-rent",
            "name": "Cobro indebido de alquiler de maquinaria propia en administración directa",
            "description": "Facturación o cobro simulado como RDR por uso de maquinaria de la propia entidad en proyectos de inversión",
            "normative_basis": "Directiva MEF de Ejecución Presupuestaria y TUO Ley de Contrataciones",
            "severity": "ALTO"
        },
        {
            "code": "contract-splitting-orders",
            "name": "Fraccionamiento de órdenes de servicio/compra menores a 8 UIT",
            "description": "Emisión de múltiples órdenes menores a 8 UIT consecutivas a un mismo proveedor para evadir licitaciones",
            "normative_basis": "Ley 30225 Art. 20, Ley 32069 y Directivas OSCE/OECE",
            "severity": "ALTO"
        },
        {
            "code": "unauthorized-budget-deviation",
            "name": "Desvío no autorizado de partidas presupuestarias entre inversión y gasto corriente",
            "description": "Modificaciones presupuestarias encubiertas sin resolución titular ni opinión de presupuesto",
            "normative_basis": "Ley 32185 de Presupuesto del Sector Público",
            "severity": "MEDIO"
        }
    ]

    with open(OUT_DIR / "municipal_typologies.json", "w", encoding="utf-8") as f:
        json.dump(typologies, f, indent=2, ensure_ascii=False)

    print(f"Artefactos curados guardados exitosamente en: {OUT_DIR}")


if __name__ == "__main__":
    main()
