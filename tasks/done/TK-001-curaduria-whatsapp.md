# TK-001: Curaduría de Datos y Filtrado de Ruido de WhatsApp

**Estado:** DONE  
**Agente Delegado:** `chat-curator`  
**Épica:** E1 - Ingesta de Evidencia Municipal y Filtrado de Ruido  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Procesar la carpeta `Chat de WhatsApp con Gestión Municipal Oficial`:
1. Clasificar y discriminar el 100% de los 234 archivos existentes.
2. Catalogar como **Ruido** 62 archivos: 53 stickers `.webp` (`STK-*`), audios/videos meméticos y tarjetas de contacto sin valor técnico.
3. Catalogar como **Alto Valor** 171 archivos: 57 directivas normativas PDF (MEF, SERVIR, Contraloría), actas DOCX y resoluciones.
4. Parsear 2,681 mensajes de chat, anonimizando números de teléfono peruanos.
5. Extraer 222 hilos técnicos sustantivos sobre administración directa, alquiler de maquinaria, malversación de fondos y fraccionamiento.

## 2. Criterios de Aceptación
- [x] Generación de `data/curated/noise_inventory.json` con el inventario de archivos descartados.
- [x] Generación de `data/curated/valuable_documents.json` con la clasificación de directivas y leyes.
- [x] Generación de `data/curated/chat_signals.json` con los 222 hilos técnicos anonimizados.
- [x] Generación de `data/curated/training_dataset_qa.jsonl` con pares de entrenamiento/evaluación para el LLM.

## 3. Evidencia
- Script ejecutable: `scripts/curate_municipal_chat.py`.
- 100% de artefactos JSON generados y validados.
