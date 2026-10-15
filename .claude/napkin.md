---
source: ai
generator: codex
generated_at: 2026-10-15T03:40:00Z
confidence: high
verified: false
---

# Napkin Runbook

## Curation Rules
- Re-prioritize on every read.
- Keep recurring, high-value notes only.
- Max 10 items per category.
- Each item includes date + "Do instead".

## Execution & Validation
1. **[2026-10-13] Tests can regenerate the verified snapshot.**
   Do instead: inspect Git status after pytest and restore only test-generated artifacts.

## Shell & Command Reliability
1. **[2026-10-13] PowerShell does not support Bash brace expansion.**
   Do instead: pass explicit paths to `rg` or use a PowerShell file iteration.

## Domain Behavior Guardrails
1. **[2026-10-13] Never expose raw red flags or citizen reports publicly.**
   Do instead: enforce access in the API as well as Supabase RLS.

## User Directives
1. **[2026-10-15] Accepted ADRs are immutable.**
   Do instead: write a new proposed ADR with supersedes when a decision needs to change.
