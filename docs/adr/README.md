# Decisiones de arquitectura — cajamarca-qhaway

Registro inmutable. Formato MADR. Plantilla: `brain/00-meta/templates/t-adr.md`.

## Reglas

1. **Los ADR no se editan.** Si una decisión cambia, se crea un ADR nuevo con `supersedes`
   y el anterior pasa a `status: superseded`. El registro histórico es todo el valor.
2. Numeración correlativa de cuatro dígitos. **Un número nunca se reutiliza**, ni aunque el
   ADR se rechace.
3. Mínimo dos opciones reales. Una opción de paja invalida el ADR.
4. Las consecuencias **negativas** son obligatorias. Sin ellas, el ADR no está terminado.
5. Un ADR rechazado se conserva: saber qué se descartó y por qué evita reabrir el debate.
6. Los agentes IA redactan en `status: proposed`. Solo un humano pasa a `accepted`.

## Cuándo escribir uno

Todo cambio arquitectónico irreversible o caro de revertir: elección de almacén de datos,
límites entre servicios, protocolo público, modelo de autenticación, dependencia
estructural.

Ante la duda, escríbelo. Un ADR cuesta veinte minutos; hacer arqueología de código para
reconstruir el porqué cuesta días.

## Índice

| # | Título | Estado | Fecha |
|---|---|---|---|
| | | | |
